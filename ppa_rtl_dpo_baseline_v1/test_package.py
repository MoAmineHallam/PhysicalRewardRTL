#!/usr/bin/env python3
"""Unit tests for the preparation-only PPA-RTL DPO package."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ppa_rtl_dpo_baseline_v1 import prepare_data, validate


HERE = Path(__file__).resolve().parent


def label(slot_id: str, design: str, source: str, rtl: str, fmax: float) -> dict:
    return {
        "slot_id": slot_id,
        "design": design,
        "source": source,
        "oracle_checks": [
            {"seed": 1, "n": 1024, "correct": True},
            {"seed": 2, "n": 1024, "correct": True},
        ],
        "eda_attempted": True,
        "rtl": rtl,
        "rtl_sha256": prepare_data.sha_text(rtl),
        "fmax_mhz": fmax,
    }


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
        cls.plan = json.loads((HERE / "label_plan.json").read_text(encoding="utf-8"))
        cls.audit = json.loads((HERE / "existing_rows_audit.json").read_text(encoding="utf-8"))

    def test_full_preparation_validator_passes(self):
        report = validate.validate(HERE / "config.json")
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["generation_or_oracle_or_eda_or_training_performed"])

    def test_label_plan_regenerates_exactly(self):
        self.assertEqual(prepare_data.generate_plan(self.config), self.plan)
        self.assertEqual(self.plan["candidate_slots"], 229)
        self.assertEqual(self.plan["selected_prompts"], 46)
        self.assertEqual(self.plan["family_counts"], {"fir": 8, "firr": 8,
                                                       "iir": 14, "med": 1,
                                                       "poly": 15})

    def test_existing_rows_are_audit_only(self):
        self.assertEqual(prepare_data.audit_existing(self.config), self.audit)
        self.assertEqual(self.audit["rows"], 229)
        self.assertEqual(self.audit["held_out_rows"], 0)
        self.assertFalse(self.audit["scientifically_valid_for_dpo_construction"])
        self.assertEqual(self.audit["consistency_errors"], [])

    def test_preference_builder_selects_best_and_worst_including_zero_failure(self):
        plan = {
            "slots": [
                {"slot_id": "d/reference", "design": "d", "source": "catalog_reference"},
                {"slot_id": "d/sft_1", "design": "d", "source": "sft_v6c_out"},
                {"slot_id": "d/sft_2", "design": "d", "source": "sft_v6c_out"},
            ],
            "prompts": [{"design": "d", "prompt": "prompt",
                         "prompt_sha256": prepare_data.sha_text("prompt")}],
        }
        rows = [
            label("d/reference", "d", "catalog_reference", "slow", 30.0),
            label("d/sft_1", "d", "sft_v6c_out", "fast", 100.0),
            label("d/sft_2", "d", "sft_v6c_out", "failed", 0.0),
        ]
        pairs = prepare_data.build_preferences(self.config, plan, rows)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["chosen"], "fast")
        self.assertEqual(pairs[0]["rejected"], "failed")
        self.assertEqual(pairs[0]["chosen_normalized"], 1.0)
        self.assertEqual(pairs[0]["rejected_normalized"], 0.0)

    def test_preference_builder_rejects_incomplete_budget(self):
        plan = {
            "slots": [
                {"slot_id": "d/reference", "design": "d", "source": "catalog_reference"},
                {"slot_id": "d/sft_1", "design": "d", "source": "sft_v6c_out"},
            ],
            "prompts": [{"design": "d", "prompt": "p", "prompt_sha256": "h"}],
        }
        with self.assertRaises(prepare_data.DataError):
            prepare_data.build_preferences(
                self.config, plan,
                [label("d/reference", "d", "catalog_reference", "a", 1.0)],
            )

    def test_preference_builder_rejects_oracle_drift(self):
        plan = {
            "slots": [{"slot_id": "d/reference", "design": "d",
                       "source": "catalog_reference"}],
            "prompts": [{"design": "d", "prompt": "p", "prompt_sha256": "h"}],
        }
        row = label("d/reference", "d", "catalog_reference", "a", 1.0)
        row["oracle_checks"][1]["correct"] = False
        with self.assertRaises(prepare_data.DataError):
            prepare_data.build_preferences(self.config, plan, [row])

    def test_equal_extrema_emit_no_pair(self):
        plan = {
            "slots": [
                {"slot_id": "d/reference", "design": "d", "source": "catalog_reference"},
                {"slot_id": "d/sft_1", "design": "d", "source": "sft_v6c_out"},
            ],
            "prompts": [{"design": "d", "prompt": "p", "prompt_sha256": "h"}],
        }
        rows = [label("d/reference", "d", "catalog_reference", "a", 4.0),
                label("d/sft_1", "d", "sft_v6c_out", "b", 4.0)]
        self.assertEqual(prepare_data.build_preferences(self.config, plan, rows), [])

    def test_validator_rejects_official_reproduction_claim(self):
        broken = copy.deepcopy(self.config)
        broken["method_identity"]["official_reproduction"] = True
        with self.assertRaises(validate.ValidationError):
            validate.validate_config(broken)

    def test_file_hash_is_raw_bytes_not_newline_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "crlf.txt"
            payload = b"first\r\nsecond\r\n"
            path.write_bytes(payload)
            self.assertEqual(prepare_data.file_sha(path), hashlib.sha256(payload).hexdigest())
            self.assertNotEqual(prepare_data.file_sha(path),
                                hashlib.sha256(payload.replace(b"\r\n", b"\n")).hexdigest())

    def test_vivado_version_has_no_2025_1_regression(self):
        self.assertEqual(self.config["performance_labeling"]["tool"], "Vivado 2023.1")
        forbidden = "Vivado 202" + "5.1"
        for path in HERE.iterdir():
            if path.suffix.lower() in {".json", ".md", ".py"}:
                self.assertNotIn(forbidden, path.read_text(encoding="utf-8"), path.name)


if __name__ == "__main__":
    unittest.main()
