#!/usr/bin/env python3
"""Regression tests for the bounded Study 2 artifact-only extension."""

import json
import math
import unittest

import analyze_artifact_extension as extension


class ArtifactExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload, cls.provenance = extension.build_package()

    def test_exact_decomposition_identity_and_headlines(self):
        expected = {
            "sft": (0.5625, 62.88915667220684, 35.375150628116344),
            "rf": (0.5385416666666668, 172.71337021795236, 93.01334625279311),
            "mlp": (0.4989583333333334, 132.55643138732114, 66.14013607763212),
            "correctness": (0.6739583333333333, 36.61694121358608, 24.67829267207312),
        }
        arms = self.payload["decomposition"]["arms"]
        self.assertEqual(set(arms), set(expected))
        for arm, (q, mu, penalized) in expected.items():
            row = arms[arm]["all"]
            self.assertAlmostEqual(row["q_correct"], q, places=12)
            self.assertAlmostEqual(row["mu_fmax_given_correct_mhz"], mu, places=10)
            self.assertAlmostEqual(row["penalized_fmax_mhz"], penalized, places=10)
            self.assertAlmostEqual(
                row["penalized_fmax_mhz"],
                row["q_correct"] * row["mu_fmax_given_correct_mhz"],
                places=12)
            self.assertLess(abs(row["identity_residual_mhz"]), 1e-12)

    def test_structural_support_and_selection_are_deterministic(self):
        structure = self.payload["correctness_structure"]
        self.assertEqual(structure["n_common_support_designs"], 16)
        self.assertEqual(structure["selected_case"]["design"], "iir18_v7")
        self.assertAlmostEqual(
            structure["selected_case"][
                "correctness_minus_sft_conditional_fmax_mhz"],
            -86.84413243930341, places=10)
        features = structure["aggregate_features"]
        self.assertGreater(features["max_stmt_mult"]["correctness"],
                           features["max_stmt_mult"]["sft"])
        self.assertLess(features["pipe_ratio_struct"]["correctness"],
                        features["pipe_ratio_struct"]["sft"])
        self.assertLess(features["accum_struct"]["correctness"],
                        features["accum_struct"]["sft"])

    def test_best_of_n_curve_and_crossings(self):
        scopes = self.payload["best_of_n"]["scopes"]
        for row in scopes.values():
            curve = row["sft_perfect_selector_expected_fmax_mhz"]
            values = [curve[str(n)] for n in extension.BEST_OF_NS]
            self.assertTrue(all(a <= b + 1e-12
                                for a, b in zip(values, values[1:])))
        all_cross = scopes["all"]["rf_one_draw_sft_best_of_n_crossing"]
        self.assertEqual((all_cross["lower_n"], all_cross["upper_n"]), (17, 18))
        self.assertEqual(scopes["interp"][
            "rf_one_draw_sft_best_of_n_crossing"]["status"],
            "above_observed_sft_best_of_48")
        extrap_cross = scopes["extrap"][
            "rf_one_draw_sft_best_of_n_crossing"]
        self.assertEqual((extrap_cross["lower_n"], extrap_cross["upper_n"]),
                         (7, 8))

    def test_cost_axes_do_not_conflate_work_units(self):
        all_scope = self.payload["best_of_n"]["scopes"]["all"]
        cost = all_scope["sft_cost_axes"]["18"]
        self.assertEqual(cost["llm_draws_per_design"], 18)
        self.assertEqual(cost["oracle_candidate_checks_without_cache_per_design"], 18)
        self.assertEqual(cost["oracle_simulation_streams_per_design"], 36)
        self.assertAlmostEqual(
            cost["expected_raw_correct_draws_requiring_implementation_without_cache_per_design"],
            10.125, places=12)
        self.assertAlmostEqual(
            cost["expected_content_deduplicated_correct_implementations_per_design"],
            3.0781838200853247, places=12)
        self.assertLess(
            cost["expected_content_deduplicated_correct_implementations_per_design"],
            cost["expected_raw_correct_draws_requiring_implementation_without_cache_per_design"])

    def test_generated_outputs_are_exactly_current(self):
        outputs = extension.rendered_outputs()
        extension.check_outputs(outputs)
        parsed = json.loads(outputs[extension.RESULT_PATH])
        self.assertEqual(parsed["schema"], "artifact_extension_results/1")
        self.assertIn("AUTO-GENERATED", outputs[extension.PROVENANCE_PATH])


if __name__ == "__main__":
    unittest.main(verbosity=2)
