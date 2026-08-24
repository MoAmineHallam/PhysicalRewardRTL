#!/usr/bin/env python3
"""Local, GPU-free regression tests for the sealed-study artifact contracts."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

import analyze_sealed_v3 as analysis
import audit_rf_reward_eligible as reward_gate
import eval_sealed
import materialize_rf_candidates as materialize
import verify_sealed_training as training
import verify_sealed_ppa as ppa_audit

HERE = os.path.dirname(os.path.abspath(__file__))


class EvaluationTests(unittest.TestCase):
    def test_gate_samples_preserves_multiplicity_and_failures(self):
        texts = ["good-a", "good-a", "wrong", "no-module"]

        def extract(text, _design):
            if text == "no-module":
                return None
            return "module d; " + text + " endmodule"

        def score(rtl, _design, n, seed):
            self.assertEqual(n, 1024)
            self.assertIn(seed, (1, 2))
            return {"compiled": True, "correct": "wrong" not in rtl}

        def reward(_rtl):
            return 123.0, {"gate": "ok", "canon_hash": "abc"}

        distinct, summary = eval_sealed.gate_samples(
            texts, "d", 4, extract, score, reward)
        self.assertEqual(summary["n_correct"], 2)
        self.assertEqual(summary["n_extraction_failed"], 1)
        self.assertEqual(summary["n_distinct_correct"], 1)
        correct = [row for row in distinct.values() if row["correct"]]
        self.assertEqual(correct[0]["count"], 2)
        self.assertEqual(correct[0]["reward"], 123.0)

    def test_output_directory_must_be_empty(self):
        with tempfile.TemporaryDirectory(dir=HERE) as root:
            open(os.path.join(root, "partial"), "w").close()
            with self.assertRaises(eval_sealed.EvaluationError):
                eval_sealed.prepare_output(root)


class MaterializationTests(unittest.TestCase):
    @staticmethod
    def write_log(path, design, rtl):
        with open(path, "w", encoding="utf-8") as handle:
            for group in (1, 2):
                for candidate in range(8):
                    row = {"group_index": group, "design": design,
                           "cand": candidate,
                           "rtl": rtl if candidate < 7 else None}
                    handle.write(json.dumps(row) + "\n")

    def test_materializes_distinct_candidates_once(self):
        with tempfile.TemporaryDirectory(dir=HERE) as root:
            log1, log2 = os.path.join(root, "s1.jsonl"), os.path.join(root, "s2.jsonl")
            rtl = "module d(input clk); endmodule"
            self.write_log(log1, "d", rtl)
            self.write_log(log2, "d", rtl)
            out = os.path.join(root, "rtl")
            manifest_path = os.path.join(root, "manifest.json")
            result = materialize.run([log1, log2], out, manifest_path)
            self.assertEqual(result["n_distinct_candidates"], 1)
            self.assertEqual(result["n_occurrences"], 28)
            self.assertEqual(len([p for p in os.listdir(out) if p.endswith(".sv")]), 1)


class RewardEligibleGateTests(unittest.TestCase):
    @staticmethod
    def make_inputs(root, *, correct_metadata=True):
        logs = []
        canon = "canonical form"
        logged_features = {"n_stmts": 1}
        for seed in (1, 2):
            path = os.path.join(root, f"s{seed}.jsonl")
            with open(path, "w", encoding="utf-8") as handle:
                for cand in range(8):
                    correct = cand == 0
                    row = {
                        "group_index": 1,
                        "cand": cand,
                        "design": "d",
                        "rtl": ("module d; good endmodule" if correct else
                                "module d; a<=b; c<=d; broken ? endmodule"),
                        "correct": correct,
                        "reward": 10.0 if correct else 0.0,
                        "gate": "ok" if correct else "incorrect",
                        "canon_hash": (reward_gate.canon_hash(canon)
                                       if correct and correct_metadata else None),
                        "struct_features": (logged_features
                                            if correct and correct_metadata else None),
                    }
                    handle.write(json.dumps(row) + "\n")
            logs.append(path)
        prereg = {
            "study2": {
                "study_id": "rf_reward_eligible_study2",
                "training_inputs": {"rf_group_logs": [
                    {"sha256": reward_gate.sha256_file(reward_gate.Path(path))}
                    for path in logs
                ]},
                "reward_eligible_gate": {
                    "trace_vectors": 256,
                    "trace_seeds": [1, 2],
                    "frozen_expected_counts": {
                        "total_occurrences": 16,
                        "nonempty_rtl_occurrences": 16,
                        "reward_eligible_occurrences": 2,
                        "reward_eligible_distinct": 1,
                    },
                },
            }
        }
        prereg_path = os.path.join(root, "prereg.json")
        with open(prereg_path, "w", encoding="utf-8") as handle:
            json.dump(prereg, handle)
        return logs, prereg_path, canon, logged_features

    def run_gate(self, root, *, correct_metadata=True, verify_fn=None):
        logs, prereg, canon, features = self.make_inputs(
            root, correct_metadata=correct_metadata)
        return reward_gate.audit(
            [reward_gate.Path(path) for path in logs],
            reward_gate.Path(prereg),
            reward_gate.Path(os.path.join(root, "out")),
            reward_gate.Path(os.path.join(root, "manifest.json")),
            reward_gate.Path(os.path.join(root, "contract.json")),
            verify_fn=(verify_fn or (lambda _rtl, **_kwargs: {"ok": True})),
            canonicalize_fn=lambda _rtl, **_kwargs: (canon, "lexical"),
            features_fn=lambda _canon: features,
            trace_fn=lambda *_args, **_kwargs: (True, "identical"),
        )

    def test_incorrect_malformed_candidate_is_counted_but_not_contracted(self):
        with tempfile.TemporaryDirectory(dir=HERE) as root:
            result = self.run_gate(root)
            self.assertEqual(result["n"], 1)
            self.assertEqual(result["passed"], 1)
            self.assertEqual(result["rejected"], 0)
            with open(os.path.join(root, "manifest.json"), encoding="utf-8") as handle:
                manifest = json.load(handle)
            self.assertEqual(manifest["gate_counts"]["reward_eligible"], 2)
            self.assertEqual(manifest["gate_counts"]["excluded:incorrect"], 14)

    def test_correct_row_missing_reward_metadata_fails_closed(self):
        with tempfile.TemporaryDirectory(dir=HERE) as root:
            result = self.run_gate(root, correct_metadata=False)
            self.assertTrue(result["pre_contract_errors"])
            self.assertEqual(result["n"], 0)

    def test_contract_exception_is_preserved_as_structured_failure(self):
        def explode(_rtl, **_kwargs):
            raise RuntimeError("synthetic contract failure")

        with tempfile.TemporaryDirectory(dir=HERE) as root:
            result = self.run_gate(root, verify_fn=explode)
            self.assertEqual(result["passed"], 0)
            self.assertEqual(result["rejected"], 1)
            self.assertEqual(result["failures"]["RuntimeError"], 1)
            self.assertEqual(result["failure_details"][0]["type"], "RuntimeError")


class AnalysisInputTests(unittest.TestCase):
    def make_eval(self, root, include_zero_summary=True):
        manifest = {
            "p__d1__g0": {"policy": "p", "design": "d1", "family": "fir",
                            "regime": "interp", "count": 2, "n": 4,
                            "reward": 100.0}}
        with open(os.path.join(root, "fmax_manifest.json"), "w") as handle:
            json.dump(manifest, handle)
        with open(os.path.join(root, "ppa.jsonl"), "w") as handle:
            handle.write(json.dumps({"module": "p__d1__g0", "compiled": 1,
                                     "fmax_mhz": 200.0}) + "\n")
        summary = {"p": {"d1": {"n": 4}}}
        if include_zero_summary:
            summary["p"]["d2"] = {"n": 4}
        with open(os.path.join(root, "holdout_summary.json"), "w") as handle:
            json.dump(summary, handle)

    def test_zero_correct_design_is_retained(self):
        with tempfile.TemporaryDirectory(dir=HERE) as root:
            self.make_eval(root)
            result = analysis.load_eval_dir(
                root, ["d1", "d2"],
                {"d1": ("fir", "interp"), "d2": ("fir", "extrap")},
                expected_n=4, require_reward=True)
            self.assertEqual(result["d1"]["equal"], 100.0)
            self.assertEqual(result["d2"]["equal"], 0.0)
            self.assertEqual(result["d2"]["correct_rate"], 0.0)

    def test_zero_correct_design_without_summary_fails(self):
        with tempfile.TemporaryDirectory(dir=HERE) as root:
            self.make_eval(root, include_zero_summary=False)
            with self.assertRaises(analysis.AnalysisInputError):
                analysis.load_eval_dir(
                    root, ["d1", "d2"],
                    {"d1": ("fir", "interp"), "d2": ("fir", "extrap")},
                    expected_n=4, require_reward=True)

    def test_study2_contract_schema_and_precontract_errors(self):
        with tempfile.TemporaryDirectory(dir=HERE) as root:
            path = os.path.join(root, "contract.json")
            contract = {
                "n": 1,
                "passed": 1,
                "rejected": 0,
                "collisions": 0,
                "failures": {},
                "pre_contract_errors": [],
                "per_file": [
                    {"file": "x.sv", "ok": True, "rejected": False,
                     "trace_equal": True}
                ],
            }
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(contract, handle)
            self.assertTrue(analysis.load_mutation_contract(path, 1)["ok"])
            contract["pre_contract_errors"] = ["synthetic ledger mismatch"]
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(contract, handle)
            self.assertFalse(analysis.load_mutation_contract(path, 1)["ok"])


class TrainingAuditTests(unittest.TestCase):
    def test_revision6_correctness_ceiling_is_synchronized(self):
        with open(os.path.join(HERE, "preregistration.json"), encoding="utf-8") as handle:
            prereg = json.load(handle)
        self.assertEqual(prereg["revision"], 6)
        self.assertEqual(prereg["training_protocol"]["max_attempted_groups"], {
            "rf_struct": 2000, "mlp": 2000, "correctness": 15000})
        self.assertEqual(training.EXPECTED["grpo_corr_s1"]["max_groups"], 15000)
        with open(os.path.join(HERE, "run_arm.sh"), encoding="utf-8") as handle:
            launcher = " ".join(handle.read().split())
        self.assertIn(
            'correctness) TAG=corr ; MAXG=15000 ; EXTRA="--reward correctness" ;;',
            launcher)

    def test_complete_group_log_requires_unique_updates(self):
        with tempfile.TemporaryDirectory(dir=HERE) as root:
            path = os.path.join(root, "groups.jsonl")
            with open(path, "w", encoding="utf-8") as handle:
                for group in range(1, 277):
                    for candidate in range(8):
                        handle.write(json.dumps({
                            "group_index": group, "design": "d", "cand": candidate,
                            "flat": False, "update": group}) + "\n")
            result = training.audit_group_log(path)
            self.assertEqual(result["updates"], 276)
            self.assertEqual(result["groups"], 276)

            with open(path, encoding="utf-8") as handle:
                rows = [json.loads(line) for line in handle]
            for row in rows[-8:]:
                row["update"] = 275
            with open(path, "w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row) + "\n")
            with self.assertRaises(training.TrainingAuditError):
                training.audit_group_log(path)


class PPAAuditTests(unittest.TestCase):
    def test_every_manifest_candidate_requires_one_explicit_row(self):
        with tempfile.TemporaryDirectory(dir=HERE) as root:
            manifest = {
                "p__d__g0": {"design": "d"},
                "p__d__g1": {"design": "d"},
            }
            with open(os.path.join(root, "fmax_manifest.json"), "w") as handle:
                json.dump(manifest, handle)
            with open(os.path.join(root, "ppa.jsonl"), "w") as handle:
                handle.write(json.dumps({
                    "module": "p__d__g0", "compiled": 1, "fmax_mhz": 100.0,
                    "lut": 1, "ff": 1, "dsp": 0, "bram": 0, "power_w": 0.1,
                }) + "\n")
            with self.assertRaises(ppa_audit.PPAError):
                ppa_audit.verify_directory(root)


if __name__ == "__main__":
    unittest.main()
