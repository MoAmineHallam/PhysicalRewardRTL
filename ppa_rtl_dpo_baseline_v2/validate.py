#!/usr/bin/env python3
"""Metadata and gate validator for the PPA-RTL V100 amendment."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CONFIG = HERE / "config.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    need(isinstance(value, dict), f"{path} is not an object")
    return value


def validate_config(config: dict) -> None:
    need(config.get("schema_version") == 2, "wrong schema")
    need(config.get("study_id") == "ppa_rtl_dpo_baseline_v2", "wrong study")
    need(config.get("status") == "prepared_not_launched", "wrong status")
    parent = config["parent_protocol"]
    pins = {
        "config_path": ("ppa_rtl_dpo_baseline_v1/config.json",
                        "df68523614e13d29201e865531b4b3e9e0ad1d3868b481ad28bc0b3148a48c99"),
        "protocol_path": ("ppa_rtl_dpo_baseline_v1/PROTOCOL.md",
                          "db07d3e1917da428a87640a4a25ceabd9d2f136682bbc9a56c759061b56618c5"),
    }
    for key, (relative, expected) in pins.items():
        need(parent.get(key) == relative, f"wrong parent {key}")
        need(parent.get(key.replace("path", "sha256_raw")) == expected,
             f"wrong parent hash declaration for {key}")
        need(sha(REPO / relative) == expected, f"parent hash drift: {relative}")
    old = read(REPO / pins["config_path"][0])
    need(old.get("status") == "prepared_not_launched", "V1 was launched")
    need(old["matched_scope"]["eda_performance_label_budget"] == 229,
         "parent label budget drift")
    need(old["matched_scope"]["optimizer_updates_per_seed"] == 276,
         "parent update budget drift")
    execution = config["model_execution"]
    need(execution["dtype"] == "torch.float16", "dtype changed")
    need(execution["hosts"] == {
        "v100a": {"hostname": "49ed1pm9lmiqe-0", "gpu": 0,
                  "gpu_model": "Tesla V100-SXM2-32GB"},
        "v100b": {"hostname": "8cqofmihc71pg-0", "gpu": 0,
                  "gpu_model": "Tesla V100S-PCIE-32GB"},
    }, "hardware assignment changed")
    need(execution.get("no_migration") is True, "migration prohibition removed")
    need("No PPA-RTL" in config.get("launcher_boundary", ""),
         "metadata package accidentally authorizes launch")


def validate_gate(config: dict) -> None:
    gate = config["timing_gate"]
    manifest = REPO / gate["candidate_manifest_path"]
    digest_file = REPO / gate["candidate_manifest_sha256_path"]
    v1_manifest = REPO / gate["v1_manifest_path"]
    result_path = REPO / gate["result_path"]
    for path in (manifest, digest_file, v1_manifest, result_path):
        need(path.is_file(), f"missing gate input: {path}")
    digest = gate["expected_candidate_package_sha256"]
    need(digest_file.read_text(encoding="ascii").split()[0] == digest,
         "candidate digest file drift")
    need(sha(manifest) == digest, "candidate manifest drift")
    need(sha(v1_manifest) == gate["expected_v1_manifest_sha256"],
         "V1 candidate manifest drift")
    result = read(result_path)
    exact = {
        "schema_version": 1, "study_id": "timing_closure_candidate_v7",
        "scope": "pilot_10", "vivado_version": "2026.1",
        "candidate_package_sha256": digest,
        "v1_manifest_sha256": gate["expected_v1_manifest_sha256"],
        "expected_candidates": 10, "completed_candidates": 10,
        "verdict": "PASS",
    }
    for key, value in exact.items():
        need(result.get(key) == value, f"gate {key} is not {value!r}")
    need(result.get("failures") == [], "gate has failures")
    for criterion in gate["required_criteria"]:
        need(result.get("criteria", {}).get(criterion) is True,
             f"gate criterion failed: {criterion}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("config", "gate"), default="config")
    args = parser.parse_args()
    try:
        config = read(CONFIG)
        validate_config(config)
        if args.mode == "gate":
            validate_gate(config)
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f"PPA-RTL V2 validation error: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: PPA-RTL V2 {args.mode} validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
