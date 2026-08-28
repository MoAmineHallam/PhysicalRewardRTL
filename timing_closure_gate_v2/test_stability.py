#!/usr/bin/env python3
"""CPU-only checks for timing-gate v2 stability helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from timing_closure_gate_v2.stability_common import (
    measurement_valid, raw_dependency_snapshot, sha256_file,
)


class StabilityTests(unittest.TestCase):
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
