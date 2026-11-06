"""FAM-2.13–2.18 — the properties no other file carries: no stream, no mutation, no import.

`docs/L2/features/surface.md` §1 (the five shared rules), `docs/L2/features/encodings.md`
§2 and §5, `docs/L3/features/layout.md` §3, ASM-2, D-13.  Nothing asserted here is
visible in a returned value, which is exactly why these properties have a file of their
own:

* no entry point draws randomness, seeds or advances the global `random` stream, because
  `engine.new_hand` is the project's single seeding point (surface.md §1 rule 3, ASM-2);
* every name is a function of its arguments alone, so two calls are equal (rule 3,
  `docs/L1/e2e-surface.md` §2);
* `encode` neither mutates the readout it was handed nor returns one array twice
  (surface.md §6, `battery.md` §3 FAM-16 case FAM-16.9);
* the import boundary is a hard rule: `import features` leaves `pokerkit` and every other
  project module absent from `sys.modules` (layout.md §3, D-13).  It is measured in a
  **fresh child interpreter** and not by an in-process check, because an in-process check
  measures pytest's collection order rather than this package's imports.

Every readout here is `engine.readout`'s own at a real decision, and every one is built
before the stream is snapshotted, so the deal the engine made cannot be mistaken for
randomness drawn by `features`.
"""

import copy
import json
import os
import random
import subprocess
import sys
import unittest

try:  # collected as part of a package
    from . import _join_support as S
except ImportError:  # collected as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _join_support as S  # noqa: E402

# layout.md §3: the project modules `features` must never import, and the libraries it
# must never need — the deal is the engine's and the tensors are a learner's.
FORBIDDEN = ("pokerkit", "torch", "engine", "agents", "evaluation", "training", "harness")

# The child interpreter's whole job: put `src` on the path, import the package, and
# report what it left loaded.
CHILD = """
import json
import sys

sys.path.insert(0, %(src)r)
import features

names = [name for name in %(names)r if callable(getattr(features, name, None))]
print(json.dumps({"names": names, "modules": sorted(sys.modules)}))
"""


class Purity(S.JoinCase):
    """The shared rules of surface.md §1, and the import boundary of layout.md §3."""

    def test_fam2_13_no_entry_point_advances_the_global_random_stream(self):
        """FAM-2.13 none of the seven draws randomness or advances the stream (§1 rule 3)."""
        readout = self.readout(self.new_hand(S.SEED_ENCODE))
        flat = self.encoder("flat-numeric")
        tokens = self.encoder("card-tokens")
        calls = {
            "encodings": [lambda: self.ep("encodings")()],
            "build_encoder": [
                lambda: self.ep("build_encoder")("flat-numeric"),
                lambda: self.ep("build_encoder")("card-tokens"),
            ],
            "observation_spec": [
                lambda: self.ep("observation_spec")(flat),
                lambda: self.ep("observation_spec")(tokens),
            ],
            "encode": [
                lambda: self.ep("encode")(flat, readout),
                lambda: self.ep("encode")(tokens, readout),
            ],
            "action_space": [lambda: self.ep("action_space")()],
            "legal_indices": [lambda: self.ep("legal_indices")(readout["legal"])],
            "decode_action": [
                lambda: self.ep("decode_action")(index) for index in S.ACTION_INDICES
            ],
        }
        self.assertEqual(
            set(calls),
            set(S.ENTRY_POINTS),
            "the battery exercises every one of the seven names (surface.md §1): %r"
            % (sorted(calls),),
        )
        # The anchor is a *mid-stream* state, taken after two draws, and the stream is
        # put back on it before every call: a name that draws, or that seeds the stream
        # to one of its own values, leaves a state that is not this one.
        random.random()
        random.random()
        anchor = random.getstate()
        for name in S.ENTRY_POINTS:
            for position, call in enumerate(calls[name]):
                with self.subTest(entry_point=name, call=position):
                    random.setstate(anchor)
                    call()
                    after = random.getstate()
                    self.assertEqual(
                        S.canonical(anchor),
                        S.canonical(after),
                        "%s must leave the global random stream as it found it, because "
                        "engine.new_hand is the project's single seeding point and this "
                        "module takes no seed (surface.md §1 rule 3, ASM-2)" % (name,),
                    )
        random.setstate(anchor)

    def test_fam2_14_one_readout_encodes_to_one_fresh_observation(self):
        """FAM-2.14 two encode calls are equal and are two arrays (surface.md §6)."""
        readout = self.readout(self.new_hand(S.SEED_DECODE))
        for name in S.ENCODING_NAMES:
            encoder = self.encoder(name)
            first = self.encode(encoder, readout)
            second = self.encode(encoder, readout)
            with self.subTest(encoding=name):
                self.assert_observation(name, self.observation_spec(encoder), first)
                self.assertTrue(
                    S.same_observation(first, second),
                    "%r is a function of its arguments alone: one readout encodes to one "
                    "observation value for value (surface.md §6, §1 rule 3)" % (name,),
                )
                self.assertIsNot(
                    first,
                    second,
                    "each call returns its own array, so a caller's mutation of one "
                    "observation cannot reach the next (surface.md §6): %r" % (name,),
                )

    def test_fam2_15_encode_does_not_mutate_the_readout_it_was_handed(self):
        """FAM-2.15 encode leaves its readout as it found it (surface.md §6, FAM-16.9)."""
        readouts = self.samples()
        self.assertGreaterEqual(
            len(readouts), 4, "the case needs several real readouts to encode"
        )
        for name in S.ENCODING_NAMES:
            encoder = self.encoder(name)
            for position, readout in enumerate(readouts):
                # The engine returns fresh containers on every readout call, so only a
                # snapshot taken before the encode can show a mutation of this one.
                snapshot = copy.deepcopy(readout)
                with self.subTest(encoding=name, decision=position):
                    self.encode(encoder, readout)
                    self.assertEqual(
                        S.canonical(snapshot),
                        S.canonical(readout),
                        "%r must not mutate the readout it was handed, because the same "
                        "readout is encoded by both encodings and read again by its "
                        "caller (surface.md §6, §1 rule 3): %r"
                        % (name, readout),
                    )
                    self.assertEqual(
                        set(readout),
                        set(S.READOUT_FACTS),
                        "the readout keeps its own ten facts through an encode "
                        "(engine/environment.md §2, surface.md §6): %r"
                        % (sorted(str(key) for key in readout),),
                    )

    def test_fam2_16_every_name_is_deterministic_across_repeated_calls(self):
        """FAM-2.16 two calls of one name return equal values (surface.md §1 rule 3)."""
        readout = self.readout(self.new_hand(S.SEED_MASK))
        encoder = self.encoder("card-tokens")
        pairs = {
            "encodings": (self.ep("encodings")(), self.ep("encodings")()),
            "build_encoder": (
                S.canonical(self.observation_spec(self.ep("build_encoder")("flat-numeric"))),
                S.canonical(self.observation_spec(self.ep("build_encoder")("flat-numeric"))),
            ),
            "observation_spec": (
                S.canonical(self.ep("observation_spec")(encoder)),
                S.canonical(self.ep("observation_spec")(self.ep("build_encoder")("card-tokens"))),
            ),
            "encode": (
                self.ep("encode")(encoder, readout).tolist(),
                self.ep("encode")(encoder, readout).tolist(),
            ),
            "action_space": (
                S.canonical(self.ep("action_space")()),
                S.canonical(self.ep("action_space")()),
            ),
            "legal_indices": (
                [int(index) for index in self.ep("legal_indices")(readout["legal"])],
                [int(index) for index in self.ep("legal_indices")(readout["legal"])],
            ),
            "decode_action": (
                [self.ep("decode_action")(index) for index in S.ACTION_INDICES],
                [self.ep("decode_action")(index) for index in S.ACTION_INDICES],
            ),
        }
        self.assertEqual(
            set(pairs),
            set(S.ENTRY_POINTS),
            "the battery calls every one of the seven names twice (surface.md §1): %r"
            % (sorted(pairs),),
        )
        for name in S.ENTRY_POINTS:
            with self.subTest(entry_point=name):
                first, second = pairs[name]
                self.assertEqual(
                    first,
                    second,
                    "%s is a function of its arguments alone, so two calls are equal "
                    "(surface.md §1 rule 3, §3–§9): %r against %r"
                    % (name, first, second),
                )

    def test_fam2_17_a_fresh_interpreter_imports_features_and_nothing_else(self):
        """FAM-2.17 `import features` leaves pokerkit and every project module absent (D-13)."""
        script = CHILD % {"src": S.src_dir(), "names": list(S.ENTRY_POINTS)}
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=S.repo_root(),
            capture_output=True,
            text=True,
            timeout=300,
        )
        self.assertEqual(
            completed.returncode,
            0,
            "a fresh interpreter must import features with %r on sys.path "
            "(layout.md §2, §3):\nstdout: %s\nstderr: %s"
            % (S.src_dir(), completed.stdout, completed.stderr),
        )
        try:
            report = json.loads(completed.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            self.fail(
                "the child interpreter reported nothing the battery can read; it printed "
                "%r and %r" % (completed.stdout, completed.stderr)
            )
        self.assertEqual(
            sorted(report["names"]),
            sorted(S.ENTRY_POINTS),
            "the fresh interpreter finds the seven declared names as callables "
            "(surface.md §1, layout.md §2): %r" % (report["names"],),
        )
        loaded = set(report["modules"])
        for name in FORBIDDEN:
            with self.subTest(module=name):
                self.assertNotIn(
                    name,
                    loaded,
                    "`import features` imports numpy and the standard library and nothing "
                    "else — never pokerkit, never torch, never a project module "
                    "(layout.md §3, module-map.md §2, D-13): the child interpreter had "
                    "%r loaded" % (name,),
                )

    def test_fam2_18_every_returned_value_is_plain_data_except_the_encoder(self):
        """FAM-2.18 the returned records are plain data; only the encoder is opaque (§1)."""
        readout = self.readout(self.new_hand(S.SEED_ENCODE))
        encoder = self.encoder("flat-numeric")
        indices = self.legal_indices(readout["legal"])
        self.assertFalse(
            S.is_plain(encoder),
            "an encoder is the one opaque value of the surface, and no caller inspects, "
            "compares or rebuilds it (surface.md §1, §4): %r" % (encoder,),
        )
        plain = {
            "encodings()": self.encodings(),
            "observation_spec(encoder)": self.observation_spec(encoder),
            "action_space()": self.action_space(),
            "legal_indices(legal)": indices,
            "decode_action(1)": self.decode_action(1),
        }
        for what, value in plain.items():
            with self.subTest(call=what):
                self.assertTrue(
                    S.is_plain(value),
                    "%s must be plain data — a mapping, a sequence of names or indices, "
                    "or a str — because a report's header quotes the vocabulary and "
                    "nothing below an entry point is surface (surface.md §1): got %r"
                    % (what, value),
                )
        observation = self.encode(encoder, readout)
        self.assertTrue(
            S.is_array(observation),
            "encode returns the observation array itself and nothing else "
            "(surface.md §6): got %r" % (type(observation).__name__,),
        )
        for position in range(len(indices)):
            with self.subTest(position=position):
                self.assertTrue(
                    S.is_count(indices[position]),
                    "a legal index is an integer and never a truthy object "
                    "(surface.md §8): %r" % (indices[position],),
                )


if __name__ == "__main__":
    unittest.main()
