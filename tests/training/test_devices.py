"""TRN-8 — the platform: `devices()`.

Drives `docs/L3/training/devices.md` §1-§3 and `docs/L2/training/surface.md` §6 (Rev 2's
measured GPU rule): the record's three keys, `cpu` first in `available` and as `default`,
the probe's record with a `reason` a reader can quote, two calls that agree, and the
identity between the names `devices()` lists and the names `run` accepts (D-8,
`strata/platform.md`).

No case requires a GPU: the platform this battery runs on reports the device nodes as
denied, and a battery may not depend on the device it is measured on (`protocol.md` §6,
`battery.md` §2). The reason is therefore asserted in whichever direction the platform
answers — a `reason` string is present either way, because "why was this run on CPU" is
the question the record exists to answer.
"""

import unittest

from _training_support import (
    INVENTED_DEVICE,
    RUN_SEED,
    TINY_BUDGET,
    TrainingCase,
    as_mapping,
    as_sequence,
    as_text,
    repeated_run,
    training,
)


class DevicesTest(TrainingCase):
    def devices(self):
        return as_mapping(training().devices(), "the device catalogue")

    def test_trn_8_1_the_catalogue_names_cpu_first_and_defaults_to_it(self):
        """TRN-8.1 `devices()` returns `{available, default, gpu}`, `available` is a sequence of names whose first is `cpu`, and `default` is `cpu` (devices.md §1, surface.md §6, D-8, FAM-1.42)."""
        catalogue = self.devices()
        self.assertEqual(
            set(catalogue),
            {"available", "default", "gpu"},
            "the record is read under `available`, `default` and `gpu` (devices.md §1, "
            "surface.md §6): %r" % (sorted(catalogue),),
        )
        available = [
            as_text(name, "a device name")
            for name in as_sequence(catalogue["available"], "'available'")
        ]
        self.assertIn(
            "cpu",
            available,
            "cpu is always present, because every rung and both table budgets run on it "
            "(devices.md §1, surface.md §6, ASM-15): %r" % (available,),
        )
        self.assertEqual(
            available[0],
            "cpu",
            "cpu is always first in `available` (devices.md §1): %r" % (available,),
        )
        self.assertEqual(
            as_text(catalogue["default"], "default"),
            "cpu",
            "the default is cpu, always — the device an omitted argument resolves to "
            "(devices.md §1, loop.md §5, D-8)",
        )
        self.assertEqual(
            len(set(available)),
            len(available),
            "a device name is listed once: %r" % (available,),
        )
        self.assertEqual(
            self.devices(),
            catalogue,
            "two calls on one platform agree, because the answer depends on the platform "
            "and not on the caller (devices.md §1, surface.md §6, FAM-1.42)",
        )

    def test_trn_8_2_the_gpu_record_carries_a_reason_whichever_way_it_answers(self):
        """TRN-8.2 `gpu` is a mapping carrying `available`, `name` and `reason`, with a `reason` string a reader can quote — whichever way the platform answers (devices.md §1-§2, surface.md §6, strata/platform.md)."""
        gpu = as_mapping(self.devices()["gpu"], "'gpu'")
        self.assertEqual(
            set(gpu),
            {"available", "name", "reason"},
            "the gpu record is `{available, name, reason}` (devices.md §1, surface.md "
            "§6): %r" % (sorted(gpu),),
        )
        self.assertIsInstance(
            gpu["available"],
            bool,
            "`gpu.available` is a boolean and not a truthy object (devices.md §1, "
            "devices.md §2's probe): %r" % (gpu["available"],),
        )
        self.assertTrue(
            gpu["name"] is None or isinstance(gpu["name"], str),
            "`gpu.name` is the hardware string when it is known statically and None "
            "otherwise, never a guess (devices.md §2): %r" % (gpu["name"],),
        )
        self.assertIsInstance(
            gpu["reason"],
            str,
            "a `reason` string is present whichever way the platform answers, because a "
            "reader quotes it for \"why was this run on CPU\" (devices.md §1-§2, "
            "strata/platform.md): %r" % (gpu["reason"],),
        )
        if not gpu["available"]:
            self.assertTrue(
                gpu["reason"].strip(),
                "an unavailable device carries the reason it is unavailable — the "
                "sandbox's denial, an absent node or the errno's name (devices.md §2, "
                "strata/platform.md): %r" % (gpu["reason"],),
            )
        self.assertIn(
            "cpu",
            [as_text(name, "a device name") for name in
             as_sequence(self.devices()["available"], "'available'")],
            "no case requires a GPU: cpu is available whatever the probe answers "
            "(devices.md §1, D-8, ASM-15)",
        )

    def test_trn_8_3_available_is_exactly_the_names_run_accepts(self):
        """TRN-8.3 `available` is the names `run` accepts: a device it lists is accepted and recorded, and a name it does not list is refused naming it (devices.md §1, §3, loop.md §5-§6, D-8)."""
        catalogue = self.devices()
        available = [
            as_text(name, "a device name")
            for name in as_sequence(catalogue["available"], "'available'")
        ]
        record = as_mapping(repeated_run(), "a run record at the default device")
        self.assertEqual(
            as_text(record["device"], "a run record's device"),
            "cpu",
            "a run naming a listed device records the device it used (devices.md §3, "
            "loop.md §3, D-8): %r" % (record["device"],),
        )
        self.assertIn(
            as_text(record["device"], "a run record's device"),
            available,
            "the device a run records is one devices() lists, so a GPU run and a CPU run "
            "are never confused (devices.md §3, protocol.md §6)",
        )
        self.assertNotIn(
            INVENTED_DEVICE,
            available,
            "the invented device name is not one the platform lists, so it is the refusal "
            "below and not an accepted name (devices.md §1)",
        )
        self.refuse(
            lambda: training().run(
                "R1", seeds=(RUN_SEED,), budget=TINY_BUDGET, device=INVENTED_DEVICE
            ),
            "UnknownDevice",
            groups=((INVENTED_DEVICE,), ("cpu",)),
            label="run at a device devices() does not list",
        )


if __name__ == "__main__":
    unittest.main()
