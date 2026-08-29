#!/usr/bin/env python3
"""Build the predeclared separate-seed VerilogEval comparison."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from common import (ProtocolError, check_environment, load_json, load_protocol,
                    raw_sha256_file, validate_complete_policy_dir,
                    validate_frozen_inputs, write_json_exclusive)


BOOTSTRAP_SEED = 20260827
BOOTSTRAP_DRAWS = 10_000


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sft-dir", required=True)
    ap.add_argument("--rf-s1-dir", required=True)
    ap.add_argument("--rf-s2-dir", required=True)
    ap.add_argument("--out-dir", required=True,
                    help="new output directory; existing paths are rejected")
    return ap


def _paired_interval(values: Any, numpy: Any) -> dict:
    array = numpy.asarray(values, dtype=float)
    if array.ndim != 1 or len(array) != 156:
        raise ProtocolError(f"paired interval requires 156 problems, observed {array.shape}")
    rng = numpy.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(0, len(array), size=(BOOTSTRAP_DRAWS, len(array)))
    replicates = array[indices].mean(axis=1)
    low, high = numpy.quantile(replicates, [0.025, 0.975], method="linear")
    return {
        "estimate": float(array.mean()),
        "ci95": [float(low), float(high)],
        "resampling_unit": "benchmark problem",
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "bootstrap_seed": BOOTSTRAP_SEED,
    }


def _metric(summary: Mapping[str, Any], name: str) -> dict[str, float]:
    return {
        problem: float(record[name])
        for problem, record in summary["by_problem"].items()
    }


def _markdown(result: Mapping[str, Any]) -> str:
    rows = [
        "# Repaired-RF VerilogEvalV2 comparison",
        "",
        "Primary endpoint: pass@1 from 20 samples on every one of the 156 "
        "official spec-to-RTL problems. Each training seed remains separate.",
        "",
        "| Policy | Training seed | pass@1 | pass@5 | pass@10 | pass@20 | Compile+verdict |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for policy in ("sft", "rf_s1", "rf_s2"):
        record = result["policies"][policy]
        rows.append(
            f"| {policy} | {record['training_seed']} | "
            f"{100 * record['pass_at_1']:.2f}% | {100 * record['pass_at_5']:.2f}% | "
            f"{100 * record['pass_at_10']:.2f}% | {100 * record['pass_at_20']:.2f}% | "
            f"{100 * record['compile_and_verdict_rate']:.2f}% |")
    rows.extend(["", "| Paired contrast | Difference (percentage points) | 95% CI |",
                 "|---|---:|---:|"])
    labels = {
        "rf_s1_minus_sft": "RF seed 1 - SFT",
        "rf_s2_minus_sft": "RF seed 2 - SFT",
        "rf_seed_mean_minus_sft": "Mean of two RF seed estimates - SFT",
    }
    for key, label in labels.items():
        record = result["paired_pass_at_1"][key]
        rows.append(
            f"| {label} | {100 * record['estimate']:.2f} | "
            f"[{100 * record['ci95'][0]:.2f}, {100 * record['ci95'][1]:.2f}] |")
    rows.extend([
        "",
        "The RF-seed mean is formed after estimating each policy separately. "
        "The 20 draws from RF seed 1 and 20 draws from RF seed 2 are not pooled "
        "into an artificial 40-draw policy.",
        "",
        "This matched V2 experiment must not be pooled with legacy n=10, "
        "temperature=0.8 VerilogEval files.",
        "",
    ])
    return "\n".join(rows)


def run(args: argparse.Namespace) -> Path:
    protocol = load_protocol()
    environment = check_environment(protocol, require_gpu=False)
    directories = {
        "sft": Path(args.sft_dir).resolve(),
        "rf_s1": Path(args.rf_s1_dir).resolve(),
        "rf_s2": Path(args.rf_s2_dir).resolve(),
    }
    configurations = {
        name: load_json(path / "run_config.json") for name, path in directories.items()
    }
    for name, config in configurations.items():
        if config.get("policy") != name:
            raise ProtocolError(f"{name} directory contains policy {config.get('policy')!r}")
    frozen_paths = {config.get("frozen_inputs_path") for config in configurations.values()}
    frozen_hashes = {config.get("frozen_inputs_raw_sha256") for config in configurations.values()}
    if len(frozen_paths) != 1 or len(frozen_hashes) != 1:
        raise ProtocolError("the three policy runs do not share one frozen-input manifest")
    frozen_path = next(iter(frozen_paths))
    frozen = validate_frozen_inputs(frozen_path, rehash_inputs=True)
    if frozen["self_raw_sha256"] != next(iter(frozen_hashes)):
        raise ProtocolError("policy run frozen-input digest mismatch")

    validated = {
        name: validate_complete_policy_dir(path, frozen)
        for name, path in directories.items()
    }
    summaries = {name: record["summary"] for name, record in validated.items()}
    problem_sets = {tuple(sorted(summary["by_problem"])) for summary in summaries.values()}
    if len(problem_sets) != 1:
        raise ProtocolError("policy summaries do not cover the identical problem set")
    problems = list(next(iter(problem_sets)))

    import numpy

    pass1 = {name: _metric(summary, "pass_at_1")
             for name, summary in summaries.items()}
    contrasts = {}
    for name in ("rf_s1", "rf_s2"):
        contrasts[f"{name}_minus_sft"] = _paired_interval(
            [pass1[name][problem] - pass1["sft"][problem] for problem in problems],
            numpy)
    contrasts["rf_seed_mean_minus_sft"] = _paired_interval(
        [(pass1["rf_s1"][problem] + pass1["rf_s2"][problem]) / 2.0 -
         pass1["sft"][problem] for problem in problems], numpy)
    contrasts["rf_s1_minus_rf_s2"] = _paired_interval(
        [pass1["rf_s1"][problem] - pass1["rf_s2"][problem]
         for problem in problems], numpy)

    metrics = ("pass_at_1", "pass_at_5", "pass_at_10", "pass_at_20",
               "compile_and_verdict_rate")
    policy_results = {}
    for name in ("sft", "rf_s1", "rf_s2"):
        policy_results[name] = {
            "training_seed": summaries[name]["training_seed"],
            **{metric: float(summaries[name]["overall"][metric]) for metric in metrics},
            "status_counts": summaries[name]["overall"]["status_counts"],
        }
    result = {
        "schema": "verilogeval_rf_comparison/1",
        "protocol_id": protocol["protocol_id"],
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "primary_metric": "pass_at_1",
        "problem_count": len(problems),
        "n_samples_per_policy_problem": 20,
        "training_seed_aggregation": (
            "each RF seed estimated separately; the RF mean averages the two "
            "per-problem estimates; raw draws are not pooled"
        ),
        "ci_scope": (
            "paired problem-level uncertainty conditional on these realized "
            "checkpoints; not an estimate of policy-training seed variance"
        ),
        "environment": environment,
        "frozen_inputs": {
            "path": frozen["self_path"],
            "raw_sha256": frozen["self_raw_sha256"],
            "benchmark_raw_dir_sha256": frozen["benchmark"]["raw_dir_sha256"],
        },
        "source_results": {
            name: {
                "directory": str(directories[name]),
                "complete_raw_sha256": raw_sha256_file(directories[name] / "final" / "COMPLETE.json"),
                "summary_raw_sha256": raw_sha256_file(directories[name] / "final" / "summary.json"),
            }
            for name in directories
        },
        "policies": policy_results,
        "paired_pass_at_1": contrasts,
    }
    output = Path(args.out_dir).resolve()
    if output.exists():
        raise ProtocolError(f"aggregate output already exists: {output}")
    output.mkdir(parents=True)
    write_json_exclusive(output / "comparison.json", result)
    (output / "comparison.md").write_text(
        _markdown(result), encoding="utf-8", newline="\n")
    print(f"wrote validated comparison -> {output}")
    return output


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        run(parser().parse_args(argv))
    except ProtocolError as exc:
        print(f"aggregate error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
