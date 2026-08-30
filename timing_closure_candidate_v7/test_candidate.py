#!/usr/bin/env python3
"""Outcome-free unit and static checks for candidate pilot V7."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from timing_closure_candidate_v7 import run_candidates as runner
from timing_closure_candidate_v7.common import (
    ROOT,
    V1_MANIFEST_SHA,
    verify_inputs,
    verify_v7_pass,
)


class CandidateV7Tests(unittest.TestCase):
    def test_frozen_candidates_and_v7_pass(self):
        manifest, digest = verify_inputs()
        self.assertEqual(digest, V1_MANIFEST_SHA)
        self.assertEqual(len(manifest["candidates"]), 10)
        self.assertEqual(
            len({row["emitted_sha256"] for row in manifest["candidates"]}),
            10,
        )
        attestation = verify_v7_pass()
        self.assertEqual(attestation["verdict"], "PASS")
        self.assertEqual(len(attestation["runs"]), 40)

    def test_exact_frozen_v1_search_is_called(self):
        from timing_closure_gate_v1 import run_closure as frozen_v1

        self.assertIs(runner.v1run.close_candidate, frozen_v1.close_candidate)
        self.assertEqual(runner.v1run.initial_periods(8.0), (6.0, 10.0))
        self.assertLessEqual(
            runner.v1run.relative_bracket_width(9.95, 10.0), 0.01
        )

    def test_command_has_new_vivado_and_short_explicit_tempdir(self):
        manifest = json.loads(
            (ROOT / "timing_closure_gate_v1" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        with tempfile.TemporaryDirectory() as temp:
            trial = runner.TrialRunnerV7(
                Path(r"C:\AMD\2026.1\Vivado\bin\vivado.bat"),
                manifest["candidates"][0],
                1,
                V1_MANIFEST_SHA,
                "a" * 64,
                Path(temp) / "results",
                Path(r"C:\VGC7P001"),
                dry_run=True,
            )
            command = trial.command(
                5.0,
                Path("result.json"),
                Path("reports"),
                Path(r"C:\VGC7P001\c01\t001\t"),
            )
        self.assertEqual(command[0], r"C:\AMD\2026.1\Vivado\bin\vivado.bat")
        self.assertIn("-tempDir", command)
        tempdir = command[command.index("-tempDir") + 1]
        self.assertTrue(tempdir.startswith(r"C:\VGC7P001"))

    def test_runner_does_not_reference_prior_result_trees(self):
        source = (
            ROOT / "timing_closure_candidate_v7" / "run_candidates.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("timing_closure_gate_v1/results", source)
        self.assertNotIn("timing_closure_candidate_v3/results", source)
        prereg = json.loads(
            (
                ROOT
                / "timing_closure_candidate_v7"
                / "preregistration.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(
            prereg["outcome_isolation"]["reuse_v1_through_v6_candidate_outcomes"]
        )

    def test_dependency_guard_detects_change(self):
        baseline = {"schema_version": 1, "aggregate_sha256_raw": "x"}
        actual = {"schema_version": 1, "aggregate_sha256_raw": "y"}
        with mock.patch.object(
            runner, "raw_dependency_snapshot", return_value=actual
        ):
            ok, _, reason = runner.dependency_guard(baseline)
        self.assertFalse(ok)
        self.assertEqual(reason, "dependency_guard_changed")


if __name__ == "__main__":
    unittest.main()
