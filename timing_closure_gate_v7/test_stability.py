#!/usr/bin/env python3
"""CPU-only checks for the prospective Vivado-2026.1 gate V7."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from timing_closure_gate_v7.run_stability_gate import (
    PROBE, RUNS, TARGET_PART, TCL,
)
from timing_closure_gate_v7.stability_common import ROOT, VIVADO_ROOT


class StabilityV7Tests(unittest.TestCase):
    def test_requires_forty_first_attempts(self):
        self.assertEqual(RUNS, 40)

    def test_uses_supported_side_by_side_install(self):
        self.assertEqual(VIVADO_ROOT, Path(r"C:\AMD\2026.1\Vivado"))
        self.assertNotEqual(VIVADO_ROOT, Path(r"C:\Xilinx\Vivado\2023.1"))

    def test_reuses_original_scientific_flow_and_probe(self):
        self.assertEqual(TCL, ROOT / "timing_closure_gate_v1" /
                         "closure_synth.tcl")
        self.assertEqual(PROBE, ROOT / "timing_closure_gate_v4" /
                         "stability_probe.sv")
        self.assertNotIn("single_thread", TCL.name)

    def test_target_is_unchanged(self):
        self.assertEqual(TARGET_PART, "xc7z020clg400-1")

    def test_v5_and_v6_remain_failed(self):
        for version in ("v5", "v6"):
            attestation = json.loads((
                ROOT / f"timing_closure_gate_{version}" /
                "stability_campaign_001" / "stability_attestation.json"
            ).read_text(encoding="utf-8"))
            self.assertEqual(attestation["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
