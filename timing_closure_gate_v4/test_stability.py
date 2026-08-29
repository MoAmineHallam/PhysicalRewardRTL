#!/usr/bin/env python3
"""CPU-only checks for timing-gate V4 stability helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from timing_closure_gate_v4.run_stability_gate import (
    RUNS, command, infrastructure_tcl_error,
)
from timing_closure_gate_v4.stability_common import (
    DEPENDENCY_RELATIVE_PATHS, measurement_valid, raw_dependency_snapshot,
    sha256_file,
)


class StabilityTests(unittest.TestCase):
    def test_v4_requires_twenty_first_attempts(self):
        self.assertEqual(RUNS, 20)

    def test_command_uses_explicit_tempdir(self):
        cmd = command(Path("vivado"), Path("result"), Path("reports"), Path("temp"))
        self.assertEqual(cmd[1:3], ["-mode", "batch"])
        self.assertIn("-tempDir", cmd)
        self.assertEqual(cmd[cmd.index("-tempDir") + 1], "temp")
        self.assertTrue(str(cmd[cmd.index("-source") + 1]).endswith(
            "timing_closure_gate_v4\\closure_synth_single_thread.tcl"))

    def test_wrapper_is_single_thread_and_sources_v1(self):
        source = (Path(__file__).resolve().parent /
                  "closure_synth_single_thread.tcl").read_text(encoding="utf-8")
        self.assertIn("set_param general.maxThreads 1", source)
        self.assertIn("timing_closure_gate_v1 closure_synth.tcl", source)

    def test_dependency_snapshot_covers_full_rt_tree(self):
        self.assertEqual(DEPENDENCY_RELATIVE_PATHS, (
            "bin/vivado.bat", "bin/unwrapped/win64.o/vivado.exe"))
        snapshot = raw_dependency_snapshot()
        paths = {row["path"] for row in snapshot["files"]}
        self.assertIn("scripts/rt/data/common.tcl", paths)
        self.assertIn("scripts/rt/fpga_tcl/rtSynthCleanup.tcl", paths)

    def test_generated_work_tcl_failure_is_infrastructure(self):
        error = "couldn't read file C:/.Xil/realtime/top.tcl: no such file or directory"
        self.assertTrue(infrastructure_tcl_error(error, ""))
    def test_raw_hash_distinguishes_newline_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lf = root / "lf.txt"
            crlf = root / "crlf.txt"
            lf.write_bytes(b"a\nb\n")
            crlf.write_bytes(b"a\r\nb\r\n")
            self.assertNotEqual(sha256_file(lf), sha256_file(crlf))

    def test_dependency_snapshot_is_stable(self):
        first = raw_dependency_snapshot()
        second = raw_dependency_snapshot()
        self.assertEqual(first, second)
        self.assertGreaterEqual(sum(row["path"].endswith(".tcl") for row in first["files"]), 1)

    def test_measurement_valid_requires_all_constraints(self):
        row = {
            "compiled": 1, "implemented": 1, "clock_count": 1,
            "setup_path_count": 1, "summary_parse_ok": 1,
            "unconstrained_path_count": 0, "route_clean": 1,
            "constraint_coverage_ok": 1, "wns_ns": 0.0,
        }
        self.assertTrue(measurement_valid(row))
        row["unconstrained_path_count"] = 1
        self.assertFalse(measurement_valid(row))


if __name__ == "__main__":
    unittest.main()
