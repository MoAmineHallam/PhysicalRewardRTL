from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))

from common import (ProtocolError, build_dataset_inventory,
                    deterministic_policy_outputs, directory_hash_pair,
                    legacy_study2_file_sha256,
                    load_protocol, pass_at_k, prepare_policy_output,
                    problem_seed, raw_sha256_file, strip_completion,
                    validate_problem_shard,
                    write_json_atomic_new)
from run_policy import make_shard


class ProtocolTests(unittest.TestCase):
    def benchmark_problem(self) -> dict:
        return {
            "prompt": {"relative_path": "Prob001_prompt.txt", "raw_sha256": "a" * 64, "bytes": 1},
            "reference": {"relative_path": "Prob001_ref.sv", "raw_sha256": "b" * 64, "bytes": 1},
            "testbench": {"relative_path": "Prob001_test.sv", "raw_sha256": "c" * 64, "bytes": 1},
        }

    def run_config(self, output: Path) -> dict:
        protocol = load_protocol()
        return {
            "schema": "verilogeval_rf_policy_run/1",
            "protocol_id": protocol["protocol_id"],
            "policy": "sft",
            "training_seed": 0,
            "generation": protocol["generation"],
            "output_dir": str(output.resolve()),
        }

    def test_frozen_protocol_identities(self) -> None:
        protocol = load_protocol()
        self.assertEqual(protocol["benchmark"]["expected_problems"], 156)
        self.assertEqual(protocol["generation"]["n_samples_per_problem"], 20)
        self.assertEqual(protocol["generation"]["temperature"], 0.85)
        self.assertEqual(protocol["generation"]["top_p"], 0.95)
        self.assertEqual(
            protocol["benchmark"]["commit"],
            "c498220d0a52248f8e3fdffe279075215bde2da6")
        self.assertEqual(
            protocol["artifacts"]["rf_s1"]["legacy_study2_dir_sha256"],
            "1e1dfe049d8b1b4ea1230c21dfad89ae378e78baee5ad762bdc115607434a959")
        self.assertEqual(protocol["benchmark"]["expected_dataset_files"], 471)
        self.assertEqual(len(protocol["benchmark"]["tracked_auxiliary_files"]), 3)
        self.assertEqual(protocol["generation"][
            "unsupported_deterministic_cuda_ops"], "warn_only")

    def test_sampling_determinism_repair_is_warn_only(self) -> None:
        source = (Path(__file__).resolve().parents[1] /
                  "run_policy.py").read_text(encoding="utf-8")
        self.assertIn(
            "torch.use_deterministic_algorithms(True, warn_only=True)", source)

    def test_raw_hash_distinguishes_line_endings_but_legacy_identity_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            left, right = root / "left", root / "right"
            left.mkdir(); right.mkdir()
            (left / "x.txt").write_bytes(b"a\r\nb\r\n")
            (right / "x.txt").write_bytes(b"a\nb\n")
            left_raw, left_legacy = directory_hash_pair(left)
            right_raw, right_legacy = directory_hash_pair(right)
            self.assertNotEqual(left_raw, right_raw)
            self.assertEqual(left_legacy, right_legacy)

    def test_new_file_hash_is_exact_raw_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "evidence.json"
            raw = b'{\r\n  "x": 1\r\n}\r\n'
            target.write_bytes(raw)
            self.assertEqual(raw_sha256_file(target), hashlib.sha256(raw).hexdigest())
            self.assertEqual(
                legacy_study2_file_sha256(target),
                hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest())
            self.assertNotEqual(raw_sha256_file(target),
                                legacy_study2_file_sha256(target))

    def test_complete_closed_dataset_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = Path(temporary)
            for problem in ("Prob001", "Prob002"):
                (dataset / f"{problem}_prompt.txt").write_text("prompt", encoding="utf-8")
                (dataset / f"{problem}_ref.sv").write_text("module ref; endmodule", encoding="utf-8")
                (dataset / f"{problem}_test.sv").write_text("module tb; endmodule", encoding="utf-8")
            auxiliaries = []
            inventory = build_dataset_inventory(dataset, 2, auxiliaries)
            self.assertEqual(inventory["problem_count"], 2)
            self.assertEqual(inventory["file_count"], 6)
            (dataset / "untracked.txt").write_text("x", encoding="utf-8")
            with self.assertRaises(ProtocolError):
                build_dataset_inventory(dataset, 2, auxiliaries)

    def test_exact_tracked_auxiliary_is_hashed_but_not_a_problem(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            dataset = Path(temporary)
            for suffix, text in (("_prompt.txt", "prompt"),
                                 ("_ref.sv", "module ref; endmodule"),
                                 ("_test.sv", "module tb; endmodule")):
                (dataset / f"Prob001{suffix}").write_text(text, encoding="utf-8")
            auxiliary = dataset / "problems.txt"
            auxiliary.write_bytes(b"index\n")
            inventory = build_dataset_inventory(dataset, 1, [{
                "relative_path": "problems.txt",
                "raw_sha256": raw_sha256_file(auxiliary),
            }])
            self.assertEqual(inventory["problem_count"], 1)
            self.assertEqual(inventory["file_count"], 4)
            self.assertEqual(len(inventory["auxiliary_files"]), 1)
            auxiliary.write_bytes(b"changed\n")
            with self.assertRaises(ProtocolError):
                build_dataset_inventory(dataset, 1, inventory["auxiliary_files"])

    def test_problem_seed_is_stable_and_problem_specific(self) -> None:
        self.assertEqual(problem_seed(20260827, "Prob001"),
                         problem_seed(20260827, "Prob001"))
        self.assertNotEqual(problem_seed(20260827, "Prob001"),
                            problem_seed(20260827, "Prob002"))

    def test_pass_at_k(self) -> None:
        self.assertAlmostEqual(pass_at_k(20, 4, 1), 0.2)
        self.assertEqual(pass_at_k(20, 1, 20), 1.0)
        self.assertEqual(pass_at_k(20, 0, 10), 0.0)
        with self.assertRaises(ProtocolError):
            pass_at_k(20, 21, 1)

    def test_strip_completion(self) -> None:
        raw = "explanation\n```verilog\nmodule TopModule; endmodule\nmodule X; endmodule\n```"
        self.assertEqual(strip_completion(raw), "module TopModule; endmodule")

    def test_shard_integrity_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "policy"
            config = self.run_config(output)
            benchmark = self.benchmark_problem()
            completions = ["module TopModule; endmodule"] * 20
            verdicts = [("PASS", "")] * 20
            shard = make_shard("Prob001", completions, verdicts, config, benchmark)
            validate_problem_shard(shard, config, benchmark)
            shard["samples"][0]["rtl"] += " "
            with self.assertRaises(ProtocolError):
                validate_problem_shard(shard, config, benchmark)

    def test_resume_skips_only_complete_valid_shards(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "policy"
            config = self.run_config(output)
            self.assertEqual(prepare_policy_output(output, config, resume=False), set())
            benchmark = self.benchmark_problem()
            shard = make_shard(
                "Prob001", ["module TopModule; endmodule"] * 20,
                [("PASS", "")] * 20, config, benchmark)
            write_json_atomic_new(output / "problems" / "Prob001.json", shard)
            self.assertEqual(prepare_policy_output(output, config, resume=True), {"Prob001"})
            with self.assertRaises(ProtocolError):
                write_json_atomic_new(output / "problems" / "Prob001.json", shard)

    def test_resume_rejects_unknown_partial_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "policy"
            config = self.run_config(output)
            prepare_policy_output(output, config, resume=False)
            (output / "partial.jsonl").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(ProtocolError):
                prepare_policy_output(output, config, resume=True)

    def test_deterministic_projection_retains_twenty_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "policy"
            config = self.run_config(output)
            prepare_policy_output(output, config, resume=False)
            benchmark = self.benchmark_problem()
            shard = make_shard(
                "Prob001", ["module TopModule; endmodule"] * 20,
                [("PASS", "")] * 4 + [("compile_fail", "bad")] * 16,
                config, benchmark)
            write_json_atomic_new(output / "problems" / "Prob001.json", shard)
            frozen = {"benchmark": {"problems": {"Prob001": benchmark}}}
            jsonl, summary = deterministic_policy_outputs(output, config, frozen)
            self.assertEqual(len(jsonl.splitlines()), 20)
            self.assertAlmostEqual(summary["overall"]["pass_at_1"], 0.2)
            self.assertEqual(summary["overall"]["total_samples"], 20)


if __name__ == "__main__":
    unittest.main()
