#!/usr/bin/env python3
"""Outcome-free unit and static checks for candidate pilot V3."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from timing_closure_candidate_v3 import run_candidates as runner
from timing_closure_candidate_v3.common import (ROOT, V1_MANIFEST_SHA,
                                                verify_inputs, verify_v3_pass)


class CandidateV3Tests(unittest.TestCase):
    def test_frozen_candidates_and_v3_pass(self):
        manifest, digest = verify_inputs()
        self.assertEqual(digest, V1_MANIFEST_SHA)
        self.assertEqual(len(manifest["candidates"]), 10)
        self.assertEqual(len({row["emitted_sha256"]
                              for row in manifest["candidates"]}), 10)
        self.assertEqual(verify_v3_pass()["verdict"], "PASS")

    def test_command_has_short_explicit_tempdir(self):
        manifest, digest = verify_inputs()
        with tempfile.TemporaryDirectory() as temp:
            trial = runner.TrialRunner(
                Path(r"C:\Xilinx\Vivado\2023.1\bin\vivado.bat"),
                manifest["candidates"][0], 1, digest, "a" * 64,
                Path(temp) / "results", Path(r"C:\VGC3P001"), dry_run=True)
            command = trial.command(5.0, Path("result.json"), Path("reports"),
                                    Path(r"C:\VGC3P001\c01\t001\t"))
        self.assertIn("-tempDir", command)
        tempdir = command[command.index("-tempDir") + 1]
        self.assertTrue(tempdir.startswith(r"C:\VGC3P001"))

    def test_initial_periods_and_gate_tolerance_unchanged(self):
        self.assertEqual(runner.v1run.initial_periods(8.0), (6.0, 10.0))
        self.assertLessEqual(runner.v1run.relative_bracket_width(9.95, 10.0),
                             0.01)

    def test_latest_monotonicity_uses_recheck(self):
        rows = [
            {"period_ns": 4.0, "valid_measurement": True, "closed": True},
            {"period_ns": 5.0, "valid_measurement": True, "closed": False},
        ]
        self.assertEqual(runner.latest_monotonic_contradictions(rows),
                         [(4.0, 5.0)])
        rows.extend([
            {"period_ns": 4.0, "valid_measurement": True, "closed": False},
            {"period_ns": 5.0, "valid_measurement": True, "closed": True},
        ])
        self.assertEqual(runner.latest_monotonic_contradictions(rows), [])

    def test_runner_does_not_reference_old_result_tree(self):
        source = (ROOT / "timing_closure_candidate_v3" /
                  "run_candidates.py").read_text(encoding="utf-8")
        self.assertNotIn("timing_closure_gate_v1/results", source)
        prereg = json.loads((ROOT / "timing_closure_candidate_v3" /
                             "preregistration.json").read_text(encoding="utf-8"))
        self.assertFalse(prereg["outcome_isolation"][
            "reuse_v1_or_v2_candidate_outcomes"])

    def test_dependency_guard_detects_change(self):
        baseline = {"schema_version": 1, "aggregate_sha256_raw": "x"}
        actual = {"schema_version": 1, "aggregate_sha256_raw": "y"}
        with mock.patch.object(runner, "raw_dependency_snapshot",
                               return_value=actual):
            ok, _, reason = runner.dependency_guard(baseline)
        self.assertFalse(ok)
        self.assertEqual(reason, "dependency_guard_changed")


if __name__ == "__main__":
    unittest.main()
