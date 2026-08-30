#!/usr/bin/env python3
"""CPU-only checks for the V5 post-restart stability package."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from timing_closure_gate_v4.run_stability_gate import PROBE, TCL
from timing_closure_gate_v5.run_stability_gate import RUNS


ROOT = Path(__file__).resolve().parent.parent


class StabilityV5Tests(unittest.TestCase):
    def test_requires_forty_first_attempts(self):
        self.assertEqual(RUNS, 40)

    def test_reuses_v4_inputs_exactly(self):
        self.assertEqual(TCL, ROOT / "timing_closure_gate_v4" /
                         "closure_synth_single_thread.tcl")
        self.assertEqual(PROBE, ROOT / "timing_closure_gate_v4" /
                         "stability_probe.sv")

    def test_v4_remains_fail(self):
        attestation = json.loads((
            ROOT / "timing_closure_gate_v4" / "stability_campaign_001" /
            "stability_attestation.json").read_text(encoding="utf-8"))
        self.assertEqual(attestation["verdict"], "FAIL")

    def test_post_restart_probe_is_diagnostic_pass(self):
        result = (ROOT / "vivado_diagnostics" / "evidence" /
                  "postrestart_20260830__r01" / "result.txt")
        self.assertEqual(result.read_text(encoding="ascii").splitlines()[0],
                         "SYNTH_PASS")


if __name__ == "__main__":
    unittest.main()
