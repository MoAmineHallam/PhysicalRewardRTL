#!/usr/bin/env python3
"""Unit checks for the seed-extension validator; no training is launched."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from seed_replication_extension_v1 import validate as subject


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads((subject.HERE / "config.json").read_text(encoding="utf-8"))

    def test_frozen_config_shape(self):
        runs = subject.validate_config(self.config)
        self.assertEqual(list(runs), list(subject.EXPECTED_RUNS))
        self.assertEqual([runs[key]["physical_gpu"] for key in runs], [7, 6, 5, 4])

    def test_frozen_command_contains_generation_batch(self):
        runs = subject.validate_config(self.config)
        command = subject.expected_command(self.config, runs["correctness_s3"])
        self.assertEqual(command[command.index("--gen-batch") + 1], "4")
        self.assertEqual(command[command.index("--seed") + 1], "3")
        self.assertEqual(command[command.index("--max-groups") + 1], "15000")

    def test_group_and_optimizer_logs_are_audited(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            group_path, optimizer_path = root / "groups.jsonl", root / "optimizer.jsonl"
            with group_path.open("w", encoding="utf-8", newline="\n") as handle:
                for group in range(1, subject.TARGET_UPDATES + 1):
                    for candidate in range(8):
                        handle.write(json.dumps({
                            "group_index": group, "step": group - 1,
                            "design": "canary", "cand": candidate,
                            "flat": False, "update": group,
                        }) + "\n")
            with optimizer_path.open("w", encoding="utf-8", newline="\n") as handle:
                for update in range(1, subject.TARGET_UPDATES + 1):
                    handle.write(json.dumps({"update": update}) + "\n")
            groups = subject.audit_jsonl(group_path, group_log=True)
            optimizer = subject.audit_jsonl(optimizer_path, group_log=False)
            self.assertEqual(groups["updates"], 276)
            self.assertEqual(groups["rows"], 276 * 8)
            self.assertEqual(optimizer["updates"], 276)

    def test_timing_gate_must_match_content_and_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            timing = root / "timing_closure_gate_v1"
            results = timing / "results"
            results.mkdir(parents=True)
            manifest = timing / "manifest.json"
            manifest.write_text('{"frozen":true}\n', encoding="utf-8", newline="\n")
            manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
            (timing / "manifest.sha256").write_text(
                f"{manifest_hash}  manifest.json\n", encoding="ascii", newline="\n")
            source = results / "candidate.json"
            source.write_text('{"status":"COMPLETE"}\n', encoding="utf-8", newline="\n")
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            gate = {
                "schema_version": 1, "study_id": "timing_closure_gate_v1",
                "scope": "pilot_10", "manifest_sha256": manifest_hash,
                "expected_candidates": 10, "completed_candidates": 10,
                "verdict": "PASS",
                "criteria": {
                    "complete_and_constrained": True, "spearman_ge_0_90": True,
                    "median_smape_le_0_15": True, "paired_direction": True,
                },
                "metrics": {
                    "spearman_rho": 0.95, "median_smape": 0.1,
                    "rf_minus_sft_mean_mhz": 1.0, "sign_reversals": 0,
                    "non_tied_pairs": 5,
                },
                "failures": [],
                "generated_from": [
                    {"path": "timing_closure_gate_v1/manifest.json",
                     "sha256": manifest_hash},
                    {"path": "timing_closure_gate_v1/results/candidate.json",
                     "sha256": source_hash},
                ],
            }
            (results / "pilot_gate.json").write_text(
                json.dumps(gate) + "\n", encoding="utf-8", newline="\n")
            config = json.loads(json.dumps(self.config))
            config["launch_prerequisites"]["timing_gate"][
                "expected_manifest_sha256"] = manifest_hash
            old_repo = subject.REPO
            try:
                subject.REPO = root
                record = subject.verify_timing_gate(config)
            finally:
                subject.REPO = old_repo
            self.assertEqual(record["manifest_sha256"], manifest_hash)
            self.assertEqual(len(record["generated_from"]), 2)


if __name__ == "__main__":
    unittest.main()
