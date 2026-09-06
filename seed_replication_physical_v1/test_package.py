import unittest
from timing_closure_gate_v1.run_closure import initial_periods
from seed_replication_physical_v1 import prepare


class PhysicalContractTests(unittest.TestCase):
    def test_population_counts(self):
        self.assertEqual(sum(1 for _ in (prepare.ROOT / "rtl/sealed_sft").glob("*.sv")), 112)
        expected = {"rf_s3": 65, "rf_s4": 43, "correctness_s2": 82}
        for policy, count in expected.items():
            self.assertEqual(sum(1 for _ in (prepare.ROOT / "seed_replication_evaluation_v1/outputs" / policy).glob("*.sv")), count)

    def test_frozen_search_bounds(self):
        self.assertEqual(initial_periods(10), (7.5, 12.5))
        self.assertEqual(initial_periods(0.5), (1.0, 0.625))
        self.assertEqual(initial_periods(300), (225.0, 200.0))

    def test_draw_denominators(self):
        self.assertEqual({p: n for p, (_, n, _) in prepare.POLICIES.items()},
                         {"sft": 48, "rf_s3": 24, "rf_s4": 24, "correctness_s2": 48})


if __name__ == "__main__":
    unittest.main()
