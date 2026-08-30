#!/usr/bin/env python3
"""CPU-only checks for the V6 persistent-parent package."""

from __future__ import annotations

import unittest
from pathlib import Path

from timing_closure_gate_v6.run_stability_gate import (
    MAX_WNS_SPREAD_NS, REQUIRED_HELPER_LAUNCHES, RUNS, command,
)

ROOT = Path(__file__).resolve().parent.parent


class StabilityV6Tests(unittest.TestCase):
    def test_gate_constants(self):
        self.assertEqual(RUNS, 40)
        self.assertEqual(REQUIRED_HELPER_LAUNCHES, 1)
        self.assertEqual(MAX_WNS_SPREAD_NS, 0.001)

    def test_one_parent_command_requests_all_iterations(self):
        cmd = command(Path("vivado"), Path("campaign"), Path("temp"))
        self.assertEqual(cmd.count("vivado"), 1)
        self.assertEqual(cmd[-2:], ["40", "xc7z020clg400-1"])
        self.assertIn("-tempDir", cmd)

    def test_tcl_uses_in_memory_project_isolation(self):
        source = (ROOT / "timing_closure_gate_v6" /
                  "persistent_closure.tcl").read_text(encoding="utf-8")
        self.assertIn("create_project -in_memory", source)
        self.assertIn("clear_current_project", source)
        self.assertIn("projects_before", source)
        self.assertIn("projects_after", source)

    def test_scientific_command_order_is_preserved(self):
        source = (ROOT / "timing_closure_gate_v6" /
                  "persistent_closure.tcl").read_text(encoding="utf-8")
        positions = [source.index(token) for token in (
            "read_xdc $xdc", "synth_design -top", "opt_design",
            "place_design", "route_design")]
        self.assertEqual(positions, sorted(positions))

    def test_two_project_diagnostic_passed(self):
        lines = (ROOT / "vivado_diagnostics" / "evidence" /
                 "persistent_project_two_run_20260830" /
                 "result.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(all("ok=1" in line and "projects_before=0" in line
                            and "projects_after=0" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
