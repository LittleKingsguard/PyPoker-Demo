"""AGT-1 — the ten entry points of the `agents` surface.

Drives `docs/L2/agents/surface.md` §1, `docs/L3/agents/README.md` §3 and
`docs/L1/e2e-surface.md` §3.3: exactly ten module-level names, in the L1 order,
and `__all__` holds none beyond them (D-12, G1).
"""

import unittest

from _agents_support import TEN_NAMES, AgentsCase


class SurfaceTest(AgentsCase):
    def test_agt1_1_the_ten_names_exist_and_are_callable(self):
        """AGT-1.1 each of the ten entry points exists and is callable (`surface.md` §1, `README.md` §3, D-12)."""
        package = self.agents()
        for name in TEN_NAMES:
            with self.subTest(entry=name):
                self.assertTrue(
                    hasattr(package, name),
                    "the agents package declares no %r entry point" % name,
                )
                self.assertTrue(
                    callable(getattr(package, name)),
                    "agents.%s exists but is not callable" % name,
                )

    def test_agt1_2_all_is_exactly_the_ten_in_the_l1_order(self):
        """AGT-1.2 `__all__` is the ten names in the L1 order and no eleventh (`README.md` §3, G1, D-12)."""
        package = self.agents()
        exported = getattr(package, "__all__", None)
        self.assertIsNotNone(exported, "the agents package declares no __all__")
        self.assertEqual(
            tuple(exported),
            TEN_NAMES,
            "__all__ must be the ten entry points in the L1 order, got %r"
            % (tuple(exported),),
        )
        self.assertEqual(
            len(exported),
            len(set(exported)),
            "__all__ repeats a name: %r" % (tuple(exported),),
        )


if __name__ == "__main__":
    unittest.main()
