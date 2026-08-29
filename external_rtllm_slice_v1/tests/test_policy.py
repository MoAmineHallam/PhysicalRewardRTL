#!/usr/bin/env python3

import sys
import unittest
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "scripts"))

from common import normalize_prompt, normalize_verilog, selection_key, sensitivity_audit  # noqa: E402


class PolicyUnitTests(unittest.TestCase):
    def test_prompt_normalization(self):
        self.assertEqual(normalize_prompt(" A\n B\tC "), "a b c")

    def test_verilog_normalization_masks_only_top_name(self):
        left = "module alpha(input clk); // x\n always @(posedge clk) begin end endmodule"
        right = "module beta ( input clk ); always@(posedge clk)begin end endmodule"
        self.assertEqual(normalize_verilog(left), normalize_verilog(right))

    def test_single_clock_and_reset(self):
        result = sensitivity_audit("always @(posedge clk or negedge rst_n) q <= d;")
        self.assertEqual(result["clock_signals"], ["clk"])
        self.assertEqual(result["reset_signals"], ["rst_n"])
        self.assertFalse(result["mixed_edge_level_sensitivities"])

    def test_mixed_edge_level_is_rejected(self):
        result = sensitivity_audit("always @(posedge clk or rst_n) q <= d;")
        self.assertTrue(result["mixed_edge_level_sensitivities"])

    def test_selection_key_is_deterministic(self):
        policy = {
            "selection_salt": "fixed",
        }
        self.assertEqual(
            selection_key(policy, "Arithmetic", "Arithmetic/X/y"),
            selection_key(policy, "Arithmetic", "Arithmetic/X/y"),
        )
        self.assertNotEqual(
            selection_key(policy, "Arithmetic", "Arithmetic/X/y"),
            selection_key(policy, "Control", "Control/X/y"),
        )


if __name__ == "__main__":
    unittest.main()
