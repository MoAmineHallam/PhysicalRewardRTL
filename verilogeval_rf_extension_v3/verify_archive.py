#!/usr/bin/env python3
"""Verify a byte-preserving relocated archive of completed V3 results.

The frozen online validator intentionally binds each policy directory to its
original absolute server path.  This verifier keeps that provenance immutable
while independently rechecking every shard, deterministic final projection,
COMPLETE hash, and aggregate statistic after the directory is copied elsewhere.
It never edits a run configuration or treats the archive path as the run path.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import aggregate  # noqa: E402
import common  # noqa: E402


EXPECTED_DIRS = {
    "sft": "sft_recovery_gpu1_20260830",
    "rf_s1": "rf_s1",
    "rf_s2": "rf_s2",
}


def need(condition: bool, message: str) -> None:
    if not condition:
        raise common.ProtocolError(message)


def same(actual: Any, expected: Any, label: str) -> None:
    need(actual == expected, f"{label}: expected {expected!r}, got {actual!r}")


def semantic_same(actual: Any, expected: Any, label: str) -> None:
    """Compare JSON semantics across Python 3.10/3.12 float reductions."""
    if isinstance(actual, dict) and isinstance(expected, dict):
        same(set(actual), set(expected), f"{label} keys")
        for key in actual:
            semantic_same(actual[key], expected[key], f"{label}.{key}")
        return
    if isinstance(actual, list) and isinstance(expected, list):
        same(len(actual), len(expected), f"{label} length")
        for index, (left, right) in enumerate(zip(actual, expected)):
            semantic_same(left, right, f"{label}[{index}]")
        return
    if isinstance(actual, float) and isinstance(expected, float):
        need(math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-15),
             f"{label}: float mismatch {actual!r} != {expected!r}")
        return
    same(actual, expected, label)


def validate_policy(directory: Path, policy: str, frozen: Mapping[str, Any],
                    protocol: Mapping[str, Any]) -> dict:
    need(directory.is_dir() and not directory.is_symlink(),
         f"missing policy archive: {directory}")
    same({entry.name for entry in directory.iterdir()},
         {"run_config.json", "problems", "final"},
         f"{policy} closed top-level file set")
    config = common.load_json(directory / "run_config.json")
    exact = {
        "schema": "verilogeval_rf_policy_run/1",
        "protocol_id": protocol["protocol_id"],
        "protocol_raw_sha256": frozen["protocol_raw_sha256"],
        "frozen_inputs_raw_sha256": frozen["self_raw_sha256"],
        "package_raw_sha256": frozen["package_raw_sha256"],
        "policy": policy,
        "training_seed": protocol["artifacts"][policy]["training_seed"],
        "base_legacy_study2_dir_sha256":
            frozen["artifacts"]["base"]["legacy_study2_dir_sha256"],
        "base_raw_dir_sha256": frozen["artifacts"]["base"]["raw_dir_sha256"],
        "adapter_legacy_study2_dir_sha256":
            frozen["artifacts"][policy]["legacy_study2_dir_sha256"],
        "adapter_raw_dir_sha256": frozen["artifacts"][policy]["raw_dir_sha256"],
        "benchmark_raw_dir_sha256": frozen["benchmark"]["raw_dir_sha256"],
        "benchmark_git_commit": frozen["benchmark"]["git_commit"],
        "generation": protocol["generation"],
        "oracle": protocol["oracle"],
    }
    for key, expected in exact.items():
        same(config.get(key), expected, f"{policy} run_config.{key}")
    original_output = config.get("output_dir")
    original_frozen = config.get("frozen_inputs_path")
    need(isinstance(original_output, str) and original_output.startswith("/home/adam/mas/mas/"),
         f"{policy} has no retained absolute server output path")
    need(isinstance(original_frozen, str) and original_frozen ==
         "/home/adam/mas/mas/verilogeval_rf_frozen_inputs_v3_20260829.json",
         f"{policy} frozen-input path changed")
    gpu = config.get("physical_gpu_index")
    environment = config.get("environment", {})
    need(isinstance(gpu, int) and gpu > 0, f"{policy} used forbidden/invalid GPU {gpu}")
    same(environment.get("cuda_visible_devices"), str(gpu),
         f"{policy} visible physical GPU")
    same(environment.get("gpu_name"), "NVIDIA L40S", f"{policy} GPU model")
    same(environment.get("gpu_compute_capability"), [8, 9],
         f"{policy} compute capability")
    same(environment.get("nvidia_driver"), "550.144.03", f"{policy} driver")
    same(environment.get("python"), "3.10.20", f"{policy} Python")
    same(environment.get("packages"), protocol["environment"]["packages"],
         f"{policy} packages")
    same(environment.get("required_environment"),
         protocol["environment"]["required_environment"],
         f"{policy} required environment")

    final = directory / "final"
    same({entry.name for entry in final.iterdir()},
         {"samples.jsonl", "summary.json", "COMPLETE.json"},
         f"{policy} closed final file set")
    projected_jsonl, projected_summary = common.deterministic_policy_outputs(
        directory, config, frozen)
    need((final / "samples.jsonl").read_bytes() == projected_jsonl,
         f"{policy} samples are not the deterministic shard projection")
    semantic_same(common.load_json(final / "summary.json"), projected_summary,
                  f"{policy} summary projection")
    complete = common.load_json(final / "COMPLETE.json")
    complete_exact = {
        "schema": "verilogeval_rf_policy_complete/1",
        "policy": policy,
        "training_seed": config["training_seed"],
        "run_config_raw_sha256": common.raw_sha256_file(directory / "run_config.json"),
        "samples_raw_sha256": common.raw_sha256_file(final / "samples.jsonl"),
        "summary_raw_sha256": common.raw_sha256_file(final / "summary.json"),
        "problem_shards_raw_dir_sha256": common.raw_directory_sha256(directory / "problems"),
    }
    for key, expected in complete_exact.items():
        same(complete.get(key), expected, f"{policy} COMPLETE.{key}")
    overall = projected_summary["overall"]
    same(overall["problem_count"], 156, f"{policy} problem count")
    same(overall["total_samples"], 3120, f"{policy} sample count")
    return {"config": config, "summary": projected_summary,
            "complete": complete, "directory": directory}


def paired_values(summaries: Mapping[str, Mapping[str, Any]]) -> dict:
    import numpy

    problem_sets = {tuple(sorted(summary["by_problem"]))
                    for summary in summaries.values()}
    need(len(problem_sets) == 1, "policies do not cover the same problems")
    problems = list(next(iter(problem_sets)))
    same(len(problems), 156, "paired problem count")
    pass1 = {
        name: {problem: float(row["pass_at_1"])
               for problem, row in summary["by_problem"].items()}
        for name, summary in summaries.items()
    }
    result = {}
    for name in ("rf_s1", "rf_s2"):
        result[f"{name}_minus_sft"] = aggregate._paired_interval(
            [pass1[name][problem] - pass1["sft"][problem]
             for problem in problems], numpy)
    result["rf_seed_mean_minus_sft"] = aggregate._paired_interval(
        [(pass1["rf_s1"][problem] + pass1["rf_s2"][problem]) / 2.0 -
         pass1["sft"][problem] for problem in problems], numpy)
    result["rf_s1_minus_rf_s2"] = aggregate._paired_interval(
        [pass1["rf_s1"][problem] - pass1["rf_s2"][problem]
         for problem in problems], numpy)
    return result


def validate_comparison(root: Path, policies: Mapping[str, dict],
                        frozen: Mapping[str, Any], protocol: Mapping[str, Any]) -> dict:
    directory = root / "comparison_recovery_gpu1_20260830"
    same({entry.name for entry in directory.iterdir()},
         {"comparison.json", "comparison.md"}, "comparison closed file set")
    result = common.load_json(directory / "comparison.json")
    exact = {
        "schema": "verilogeval_rf_comparison/1",
        "protocol_id": protocol["protocol_id"],
        "primary_metric": "pass_at_1",
        "problem_count": 156,
        "n_samples_per_policy_problem": 20,
    }
    for key, expected in exact.items():
        same(result.get(key), expected, f"comparison.{key}")
    same(result["frozen_inputs"]["raw_sha256"], frozen["self_raw_sha256"],
         "comparison frozen-input hash")
    same(result["frozen_inputs"]["benchmark_raw_dir_sha256"],
         frozen["benchmark"]["raw_dir_sha256"],
         "comparison benchmark hash")
    metrics = ("pass_at_1", "pass_at_5", "pass_at_10", "pass_at_20",
               "compile_and_verdict_rate")
    for name, record in policies.items():
        summary = record["summary"]
        expected_policy = {
            "training_seed": summary["training_seed"],
            **{metric: float(summary["overall"][metric]) for metric in metrics},
            "status_counts": summary["overall"]["status_counts"],
        }
        semantic_same(result["policies"][name], expected_policy,
                      f"comparison policy projection {name}")
        source = result["source_results"][name]
        same(source["complete_raw_sha256"], common.raw_sha256_file(
            record["directory"] / "final" / "COMPLETE.json"),
            f"comparison {name} COMPLETE source")
        same(source["summary_raw_sha256"], common.raw_sha256_file(
            record["directory"] / "final" / "summary.json"),
            f"comparison {name} summary source")
    recomputed = paired_values({name: record["summary"]
                                for name, record in policies.items()})
    for contrast, expected in recomputed.items():
        observed = result["paired_pass_at_1"][contrast]
        same(observed["bootstrap_draws"], expected["bootstrap_draws"],
             f"{contrast} bootstrap draws")
        same(observed["bootstrap_seed"], expected["bootstrap_seed"],
             f"{contrast} bootstrap seed")
        need(math.isclose(observed["estimate"], expected["estimate"],
                          rel_tol=0.0, abs_tol=1e-15),
             f"{contrast} estimate changed")
        need(all(math.isclose(a, b, rel_tol=0.0, abs_tol=1e-15)
                 for a, b in zip(observed["ci95"], expected["ci95"])),
             f"{contrast} interval changed")
    validation_log = (root / "comparison_recovery_gpu1_20260830.validation.log")
    aggregate_log = (root / "comparison_recovery_gpu1_20260830.aggregate.log")
    need(validation_log.is_file() and aggregate_log.is_file(),
         "retained validation/aggregate logs are missing")
    text = validation_log.read_text(encoding="utf-8")
    for marker in ("PASS frozen_inputs", "PASS sft", "PASS rf_s1", "PASS rf_s2"):
        need(marker in text, f"validation log lacks {marker!r}")
    need("wrote validated comparison" in aggregate_log.read_text(encoding="utf-8"),
         "aggregate log lacks success marker")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", default=str(
        HERE / "results" / "validated_20260830"))
    args = parser.parse_args()
    try:
        root = Path(args.archive_root).resolve()
        frozen_path = root / "verilogeval_rf_frozen_inputs_v3_20260829.json"
        frozen = common.validate_frozen_inputs(frozen_path, rehash_inputs=False)
        protocol = common.load_protocol()
        policies = {
            policy: validate_policy(root / dirname, policy, frozen, protocol)
            for policy, dirname in EXPECTED_DIRS.items()
        }
        comparison = validate_comparison(root, policies, frozen, protocol)
    except (OSError, ValueError, KeyError, common.ProtocolError) as exc:
        print(f"archive validation error: {exc}", file=sys.stderr)
        return 2
    print("PASS relocated VerilogEval V3 archive: 3 policies, 156 problems, "
          "9,360 samples, deterministic finals, COMPLETE hashes, and paired "
          "comparison all verified")
    print("pass@1 " + " ".join(
        f"{name}={100 * comparison['policies'][name]['pass_at_1']:.3f}%"
        for name in ("sft", "rf_s1", "rf_s2")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
