import json
import math
import tempfile
import unittest
from pathlib import Path

from timing_closure_gate_v1 import generate_manifest as gm
from timing_closure_gate_v1 import run_closure as rc
from timing_closure_gate_v1 import validate_gate as vg


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = gm.build_manifest()

    def test_deterministic_manifest(self):
        self.assertEqual(self.manifest, gm.build_manifest())
        self.assertEqual(self.manifest["scope"], "pilot_10")
        self.assertEqual(len(self.manifest["common_support_designs"]), 15)

    def test_predeclared_designs_and_candidate_count(self):
        expected = {
            "fir": "fir42_v6_8b",
            "firr": "firr20_v6",
            "iir": "iir18_v7",
            "med": "med21",
            "poly": "poly6_v13_8b",
        }
        self.assertEqual(self.manifest["selected_designs_by_family"], expected)
        candidates = self.manifest["candidates"]
        self.assertEqual(len(candidates), 10)
        self.assertEqual(len({row["candidate_id"] for row in candidates}), 10)
        self.assertEqual(len({row["source_sha256"] for row in candidates}), 10)
        for family, design in expected.items():
            rows = [row for row in candidates if row["family"] == family]
            self.assertEqual({row["arm"] for row in rows}, {"sft", "rf"})
            self.assertEqual({row["design"] for row in rows}, {design})

    def test_old_proxy_identity_and_input_hashes(self):
        for row in self.manifest["candidates"]:
            self.assertTrue(math.isclose(
                row["old_proxy_delay_ns"], 5.0 - row["old_wns_ns"],
                rel_tol=2e-4, abs_tol=2e-3))
            self.assertEqual(gm.sha256_file(gm.ROOT / row["source_path"]),
                             row["emitted_sha256"])


class SearchTests(unittest.TestCase):
    def test_initial_bracket_and_width(self):
        self.assertEqual(rc.initial_periods(10.0), (7.5, 12.5))
        self.assertAlmostEqual(rc.relative_bracket_width(9.9, 10.0),
                               0.1 / 9.95)

    def test_measurement_validation_is_fail_closed(self):
        valid = {
            "compiled": 1,
            "implemented": 1,
            "clock_count": 1,
            "setup_path_count": 1,
            "summary_parse_ok": 1,
            "unconstrained_path_count": 0,
            "route_clean": 1,
            "constraint_coverage_ok": 1,
            "wns_ns": -0.1,
        }
        self.assertTrue(rc.measurement_valid(valid))
        for key in ("compiled", "implemented", "clock_count",
                    "setup_path_count", "route_clean",
                    "constraint_coverage_ok", "summary_parse_ok"):
            broken = dict(valid)
            broken[key] = 0
            self.assertFalse(rc.measurement_valid(broken), key)
        broken = dict(valid)
        broken["unconstrained_path_count"] = -1
        self.assertFalse(rc.measurement_valid(broken))

    def test_nonmonotonicity(self):
        monotone = [
            {"period_ns": 5.0, "valid_measurement": True, "closed": False},
            {"period_ns": 6.0, "valid_measurement": True, "closed": True},
        ]
        self.assertEqual(rc.monotonic_contradictions(monotone), [])
        contradiction = monotone + [
            {"period_ns": 4.0, "valid_measurement": True, "closed": True},
            {"period_ns": 7.0, "valid_measurement": True, "closed": False},
        ]
        self.assertTrue(rc.monotonic_contradictions(contradiction))


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = gm.build_manifest()
        cls.digest = gm.sha256_bytes(gm.canonical_bytes(cls.manifest))

    def test_statistics(self):
        self.assertAlmostEqual(vg.spearman([1, 2, 3], [10, 20, 30]), 1.0)
        self.assertAlmostEqual(vg.spearman([1, 2, 3], [30, 20, 10]), -1.0)
        self.assertEqual(vg.smape(0.0, 0.0), 0.0)
        self.assertAlmostEqual(vg.smape(90.0, 100.0), 10.0 / 95.0)

    def test_static_tcl_reads_constraint_before_synthesis(self):
        vg.static_tcl_order_check()

    def test_synthetic_identity_pass(self):
        with tempfile.TemporaryDirectory(dir=gm.HERE) as temporary:
            result_root = Path(temporary)
            for candidate in self.manifest["candidates"]:
                path = result_root / candidate["candidate_id"] / "closure_result.json"
                path.parent.mkdir(parents=True)
                closure = float(candidate["old_fmax_mhz"])
                result = {
                    "schema_version": 1,
                    "study_id": "timing_closure_gate_v1",
                    "scope": "pilot_10",
                    "manifest_sha256": self.digest,
                    "candidate_id": candidate["candidate_id"],
                    "family": candidate["family"],
                    "design": candidate["design"],
                    "arm": candidate["arm"],
                    "module": candidate["module"],
                    "old_fmax_mhz": candidate["old_fmax_mhz"],
                    "status": "COMPLETE",
                    "failure_reason": None,
                    "tight_failing_period_ns": 9.95,
                    "loose_passing_period_ns": 10.0,
                    "relative_bracket_width": 0.05 / 9.975,
                    "closure_fmax_mhz": closure,
                    "closure_fmax_interval_mhz": [closure, closure * 1.01],
                    "bisections": 6,
                    "trial_count": 2,
                    "trials": [
                        {"purpose": "confirm_fail"},
                        {"purpose": "confirm_pass"},
                    ],
                }
                path.write_text(json.dumps(result), encoding="utf-8")
            gate, failures = vg.build_pilot_gate(
                self.manifest, self.digest, result_root)
            self.assertIsNotNone(gate)
            self.assertEqual(gate["verdict"], "PASS", failures)
            self.assertTrue(all(gate["criteria"].values()))

    def test_incomplete_results_do_not_form_gate(self):
        with tempfile.TemporaryDirectory(dir=gm.HERE) as temporary:
            gate, failures = vg.build_pilot_gate(
                self.manifest, self.digest, Path(temporary))
            self.assertIsNone(gate)
            self.assertEqual(len(failures), 10)


if __name__ == "__main__":
    unittest.main()
