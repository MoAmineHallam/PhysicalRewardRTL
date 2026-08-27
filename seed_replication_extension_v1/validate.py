#!/usr/bin/env python3
"""Fail-closed validator for the prospective seed-replication extension.

This file deliberately uses only the Python standard library.  The launcher
calls it before doing any GPU work; the completion mode is the only supported
way to declare the four training jobs complete.  It never launches training or
endpoint evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, Optional, Sequence


HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULT_CONFIG = HERE / "config.json"
TEXT_EXT = {
    ".bib", ".json", ".jsonl", ".md", ".ps1", ".py", ".sh", ".sv",
    ".tcl", ".txt", ".v",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_RUNS = {
    "rf_s3": ("repaired_rf", "rf_struct", 3, 7, 2000,
              "runs/grpo_rf_s3", "logs/rf_s3.optimizer.jsonl",
              "logs/rf_s3.stdout.log", "status/rf_s3.status.json"),
    "rf_s4": ("repaired_rf", "rf_struct", 4, 6, 2000,
              "runs/grpo_rf_s4", "logs/rf_s4.optimizer.jsonl",
              "logs/rf_s4.stdout.log", "status/rf_s4.status.json"),
    "correctness_s2": ("correctness_only", "correctness", 2, 5, 15000,
                       "runs/grpo_correctness_s2",
                       "logs/correctness_s2.optimizer.jsonl",
                       "logs/correctness_s2.stdout.log",
                       "status/correctness_s2.status.json"),
    "correctness_s3": ("correctness_only", "correctness", 3, 4, 15000,
                       "runs/grpo_correctness_s3",
                       "logs/correctness_s3.optimizer.jsonl",
                       "logs/correctness_s3.stdout.log",
                       "status/correctness_s3.status.json"),
}
TARGET_UPDATES = 276
CHECKPOINTS = [138, 276]


class ValidationError(RuntimeError):
    """A protocol invariant did not hold."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValidationError(f"cannot read JSON {path}: {exc}") from exc
    require(isinstance(value, dict), f"{path} is not a JSON object")
    return value


def sha256_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ValidationError(f"cannot hash {path}: {exc}") from exc
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    if path.suffix.lower() not in TEXT_EXT:
        return sha256_bytes(path)
    try:
        raw = path.read_bytes().replace(b"\r\n", b"\n")
    except OSError as exc:
        raise ValidationError(f"cannot hash {path}: {exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def sha256_dir(root: Path) -> tuple[str, int]:
    entries = []
    try:
        for path in root.rglob("*"):
            if path.is_file():
                entries.append((path.relative_to(root).as_posix(),
                                sha256_file(path)))
    except OSError as exc:
        raise ValidationError(f"cannot enumerate {root}: {exc}") from exc
    digest = hashlib.sha256()
    for relative, item_hash in sorted(entries):
        digest.update(relative.encode("utf-8") + b"\0"
                      + item_hash.encode("ascii") + b"\n")
    return digest.hexdigest(), len(entries)


def raw_sha256(path: Path) -> str:
    """Raw digest, used by the timing-gate contract and run status."""
    return sha256_bytes(path)


def legacy_all_file_lf_sha256(path: Path) -> str:
    """Reproduce grpo_oracle.py's legacy `_sha` even for binary files."""
    try:
        raw = path.read_bytes().replace(b"\r\n", b"\n")
    except OSError as exc:
        raise ValidationError(f"cannot hash {path}: {exc}") from exc
    return hashlib.sha256(raw).hexdigest()


def same_float(actual: Any, expected: float, label: str) -> None:
    try:
        matches = math.isclose(float(actual), expected,
                               rel_tol=0.0, abs_tol=1e-12)
    except (TypeError, ValueError):
        matches = False
    require(matches, f"{label}: expected {expected!r}, got {actual!r}")


def relative_extension_path(value: Any, label: str) -> Path:
    require(isinstance(value, str) and value,
            f"{label} must be a non-empty path")
    posix = PurePosixPath(value)
    require(not posix.is_absolute() and ".." not in posix.parts,
            f"{label} escapes the repository: {value!r}")
    require(posix.parts and posix.parts[0] == HERE.name,
            f"{label} must remain below {HERE.name}/: {value!r}")
    resolved = (REPO / Path(*posix.parts)).resolve()
    try:
        resolved.relative_to(HERE.resolve())
    except ValueError as exc:
        raise ValidationError(f"{label} escapes {HERE}") from exc
    return resolved


def validate_config(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    require(config.get("schema_version") == 1, "config schema_version is not 1")
    require(config.get("study_id") == "seed_replication_extension_v1",
            "wrong config study_id")
    require(config.get("status") == "prepared_not_launched",
            "config status must remain prepared_not_launched")

    separation = config.get("separation_from_prior_studies", {})
    for key in (
        "study2_primary_remains_unchanged",
        "extension_runs_must_not_be_pooled_into_the_preregistered_primary_result",
        "launch_is_training_only",
        "endpoint_generation_requires_a_separate_explicit_command_and_is_not_implemented_by_the_launcher",
    ):
        require(separation.get(key) is True, f"config separation flag {key} is not true")
    require(separation.get("extension_label") ==
            "prospective post-primary seed replication",
            "wrong extension label")

    remote = config.get("remote_execution", {})
    expected_remote = {
        "hostname": "ubuntu-SYS-420GP-TNR",
        "repo_root": "/home/adam/mas/mas/fpga",
        "allowed_parent": "/home/adam/mas/mas",
        "python": "/home/adam/mas/mas/env_fpga/bin/python",
        "environment_bin": "/home/adam/mas/mas/env_fpga/bin",
        "base_model": "/home/adam/mas/mas/rtlcoder",
        "sft_adapter": "sft_v6c_out",
        "allowed_physical_gpus": [7, 6, 5, 4],
        "minimum_repo_filesystem_free_gib": 25,
    }
    for key, expected in expected_remote.items():
        require(remote.get(key) == expected,
                f"remote_execution.{key}: expected {expected!r}, got {remote.get(key)!r}")
    require(remote.get("required_environment") == {
        "PYTHONNOUSERSITE": "1", "python": "3.10.20",
        "torch": "2.4.1+cu121", "transformers": "4.46.3",
        "peft": "0.13.2", "accelerate": "1.0.1", "numpy": "2.2.6",
        "scipy": "1.15.3", "scikit_learn": "1.7.2",
        "joblib": "1.5.3", "iverilog": "12.0",
    }, "required L40 environment versions changed")
    idle = remote.get("gpu_idle", {})
    require(idle == {
        "maximum_memory_used_mib": 128,
        "maximum_utilization_percent": 1,
        "require_no_compute_pids": True,
        "checks_immediately_before_launch": 2,
        "seconds_between_checks": 2,
    }, "GPU-idle contract changed")

    protocol = config.get("training_protocol", {})
    exact_protocol = {
        "initialization": "byte-identical sft_v6c_out adapter",
        "kl_reference": "frozen copy of the same SFT adapter",
        "optimizer": "AdamW",
        "dtype": "torch.float16",
        "group_size": 8,
        "generation_batch": 4,
        "temperature": 1.0,
        "max_tokens": 1536,
        "learning_rate": 1e-05,
        "kl_coefficient": 0.1,
        "incorrect_reward": 0.0,
        "target_nonflat_updates": TARGET_UPDATES,
        "checkpoints_at_updates": CHECKPOINTS,
        "rf_max_attempted_groups": 2000,
        "correctness_max_attempted_groups": 15000,
    }
    for key, expected in exact_protocol.items():
        require(protocol.get(key) == expected,
                f"training_protocol.{key}: expected {expected!r}, got {protocol.get(key)!r}")
    require(protocol.get("optimizer_defaults") == {
        "betas": [0.9, 0.999], "eps": 1e-08, "weight_decay": 0.01,
    }, "optimizer defaults changed")
    require("never resume" in str(protocol.get("crash_policy", "")),
            "crash policy no longer forbids resume")

    by_id: Dict[str, Dict[str, Any]] = {}
    runs = config.get("runs")
    require(isinstance(runs, list) and len(runs) == 4,
            "config must contain exactly four runs")
    all_paths = set()
    for run in runs:
        require(isinstance(run, dict), "a run entry is not an object")
        run_id = run.get("run_id")
        require(run_id in EXPECTED_RUNS and run_id not in by_id,
                f"unexpected or duplicate run_id {run_id!r}")
        condition, reward, seed, gpu, ceiling, output_tail, opt_tail, stdout_tail, status_tail = EXPECTED_RUNS[run_id]
        exact = {
            "condition": condition, "reward": reward,
            "reward_artifact": "rf_struct.joblib" if reward == "rf_struct" else None,
            "training_seed": seed, "physical_gpu": gpu,
            "max_attempted_groups": ceiling,
            "output_dir": f"{HERE.name}/{output_tail}",
            "optimizer_log": f"{HERE.name}/{opt_tail}",
            "stdout_log": f"{HERE.name}/{stdout_tail}",
            "status_file": f"{HERE.name}/{status_tail}",
        }
        for key, expected in exact.items():
            require(run.get(key) == expected,
                    f"{run_id}.{key}: expected {expected!r}, got {run.get(key)!r}")
        for key in ("output_dir", "optimizer_log", "stdout_log", "status_file"):
            resolved = relative_extension_path(run[key], f"{run_id}.{key}")
            require(resolved not in all_paths, f"duplicate output path: {resolved}")
            all_paths.add(resolved)
        by_id[run_id] = run
    require(set(by_id) == set(EXPECTED_RUNS), "the frozen run set changed")

    prerequisites = config.get("launch_prerequisites", {})
    for key in (
        "all_required_artifact_hashes_match",
        "run_arm_sh_must_remain_unchanged",
        "every_selected_run_assigned_gpu_must_be_idle",
        "every_extension_output_log_and_status_path_must_be_absent",
    ):
        require(prerequisites.get(key) is True,
                f"launch prerequisite {key} is not true")
    require("all_four_assigned_gpus_must_be_idle" not in prerequisites,
            "obsolete all-four GPU prerequisite must not reappear")
    gate = prerequisites.get("timing_gate", {})
    expected_gate = {
        "result_path": "timing_closure_gate_v1/results/pilot_gate.json",
        "manifest_sha256_path": "timing_closure_gate_v1/manifest.sha256",
        "schema_version": 1,
        "study_id": "timing_closure_gate_v1",
        "scope": "pilot_10",
        "expected_candidates": 10,
        "required_verdict": "PASS",
        "required_criteria": [
            "complete_and_constrained", "spearman_ge_0_90",
            "median_smape_le_0_15", "paired_direction",
        ],
    }
    for key, expected in expected_gate.items():
        require(gate.get(key) == expected,
                f"timing gate {key}: expected {expected!r}, got {gate.get(key)!r}")
    require(bool(HEX64.fullmatch(str(gate.get("expected_manifest_sha256", "")))),
            "timing gate manifest digest is not pinned to 64 lowercase hex characters")

    evaluation = config.get("prospective_evaluation_contract_not_launched_here", {})
    require(evaluation.get("status") ==
            "frozen_for_a_later_separate_evaluation_launcher",
            "endpoint contract is not explicitly separated")
    require(evaluation.get("checkpoint") == 276, "endpoint checkpoint changed")
    require(evaluation.get("rf_samples_per_design_per_seed") == 24,
            "RF endpoint multiplicity changed")
    require(evaluation.get("correctness_samples_per_design_per_seed") == 48,
            "correctness endpoint multiplicity changed")
    require(evaluation.get("generation_seed_rule") == "100 + training_seed",
            "generation-seed rule changed")
    require(evaluation.get("rf_generation_seeds") == {"3": 103, "4": 104},
            "RF generation seeds changed")
    require(evaluation.get("correctness_generation_seeds") == {"2": 102, "3": 103},
            "correctness generation seeds changed")
    require(evaluation.get("multiplicity_retained") is True,
            "endpoint multiplicity must be retained")
    return by_id


def verify_dependencies(config: Dict[str, Any], require_server: bool) -> list[dict]:
    frozen = config.get("frozen_dependencies", {})
    identity = frozen.get("identity_manifest", {})
    manifest_path = REPO / str(identity.get("path", ""))
    require(manifest_path.is_file(), f"identity manifest missing: {manifest_path}")
    require(sha256_file(manifest_path) == identity.get("sha256"),
            f"{manifest_path.name} has drifted from its extension pin")
    manifest = read_json(manifest_path).get("hashes", {})
    require(isinstance(manifest, dict), f"{manifest_path.name} lacks a hashes object")

    records = []
    items = frozen.get("items")
    require(isinstance(items, list) and items, "no frozen dependencies declared")
    for item in items:
        require(isinstance(item, dict), "malformed dependency entry")
        expected = str(item.get("sha256", ""))
        require(bool(HEX64.fullmatch(expected)),
                f"invalid expected digest for {item.get('path')}")
        key = item.get("manifest_key")
        require(manifest.get(key) == expected,
                f"extension pin disagrees with {manifest_path.name} for {key}")
        raw_path = str(item.get("path", ""))
        path = Path(raw_path) if os.path.isabs(raw_path) else REPO / raw_path
        if not path.exists():
            if item.get("availability") == "server_only" and not require_server:
                records.append({"path": raw_path, "status": "server_only_not_checked"})
                continue
            raise ValidationError(f"frozen dependency missing: {path}")
        kind = item.get("kind")
        if kind == "file":
            require(path.is_file(), f"dependency is not a file: {path}")
            actual, n_files = sha256_file(path), None
        elif kind == "directory":
            require(path.is_dir(), f"dependency is not a directory: {path}")
            actual, n_files = sha256_dir(path)
            require(n_files == item.get("n_files"),
                    f"directory file count drift for {path}: {n_files} != {item.get('n_files')}")
            manifest_count = manifest.get(f"{key}::n_files")
            if manifest_count is not None:
                require(n_files == manifest_count,
                        f"directory count disagrees with {manifest_path.name} for {key}")
        else:
            raise ValidationError(f"unknown dependency kind {kind!r} for {path}")
        require(actual == expected,
                f"dependency drift: {path}; expected {expected}, got {actual}")
        legacy_expected = item.get("legacy_run_config_lf_normalized_binary_sha256")
        if legacy_expected is not None:
            require(bool(HEX64.fullmatch(str(legacy_expected))),
                    f"invalid legacy run-config digest for {path}")
            legacy_actual = legacy_all_file_lf_sha256(path)
            require(legacy_actual == legacy_expected,
                    f"legacy run-config digest mismatch for {path}")
        records.append({"path": raw_path, "sha256": actual,
                        "n_files": n_files, "status": "verified"})
    return records


def verify_timing_gate(config: Dict[str, Any]) -> Dict[str, Any]:
    gate_cfg = config["launch_prerequisites"]["timing_gate"]
    digest_path = REPO / gate_cfg["manifest_sha256_path"]
    manifest_path = digest_path.with_name("manifest.json")
    result_path = REPO / gate_cfg["result_path"]
    for path in (digest_path, manifest_path, result_path):
        require(path.is_file(), f"timing gate prerequisite missing: {path}")
    try:
        digest_tokens = digest_path.read_text(encoding="ascii").split()
    except OSError as exc:
        raise ValidationError(f"cannot read {digest_path}: {exc}") from exc
    require(digest_tokens and HEX64.fullmatch(digest_tokens[0]) is not None,
            f"malformed timing digest file: {digest_path}")
    digest = digest_tokens[0]
    expected_digest = gate_cfg["expected_manifest_sha256"]
    require(digest == expected_digest,
            f"timing manifest digest differs from extension pin: {digest} != {expected_digest}")
    require(raw_sha256(manifest_path) == digest,
            "timing manifest content does not match manifest.sha256")

    result = read_json(result_path)
    exact = {
        "schema_version": gate_cfg["schema_version"],
        "study_id": gate_cfg["study_id"],
        "scope": gate_cfg["scope"],
        "manifest_sha256": digest,
        "expected_candidates": gate_cfg["expected_candidates"],
        "completed_candidates": gate_cfg["expected_candidates"],
        "verdict": gate_cfg["required_verdict"],
    }
    for key, expected in exact.items():
        require(result.get(key) == expected,
                f"timing result {key}: expected {expected!r}, got {result.get(key)!r}")
    criteria = result.get("criteria")
    require(isinstance(criteria, dict), "timing result lacks criteria object")
    for key in gate_cfg["required_criteria"]:
        require(criteria.get(key) is True, f"timing gate criterion did not pass: {key}")
    require(result.get("failures") == [], "timing gate reports failures")
    metrics = result.get("metrics")
    require(isinstance(metrics, dict), "timing gate lacks metrics object")
    for key in ("spearman_rho", "median_smape", "rf_minus_sft_mean_mhz",
                "sign_reversals", "non_tied_pairs"):
        require(key in metrics and metrics[key] is not None,
                f"timing gate metric is missing/null: {key}")

    sources = result.get("generated_from")
    require(isinstance(sources, list) and sources,
            "timing gate lacks non-empty generated_from provenance")
    verified_sources = []
    for index, source in enumerate(sources):
        require(isinstance(source, dict), f"generated_from[{index}] is malformed")
        raw_path, expected = source.get("path"), source.get("sha256")
        require(isinstance(raw_path, str) and raw_path,
                f"generated_from[{index}] has no path")
        require(isinstance(expected, str) and HEX64.fullmatch(expected) is not None,
                f"generated_from[{index}] has invalid digest")
        candidate = Path(raw_path)
        candidates = ([candidate] if candidate.is_absolute() else
                      [REPO / candidate, result_path.parent / candidate,
                       result_path.parent.parent / candidate])
        existing = next((path for path in candidates if path.is_file()), None)
        require(existing is not None,
                f"generated_from artifact cannot be resolved: {raw_path}")
        actual = raw_sha256(existing)
        require(actual == expected,
                f"generated_from hash mismatch for {existing}: {actual} != {expected}")
        verified_sources.append({"path": str(existing), "sha256": actual})
    return {"path": str(result_path), "sha256": raw_sha256(result_path),
            "manifest_sha256": digest, "metrics": metrics,
            "generated_from": verified_sources}


def select_runs(by_id: Dict[str, Dict[str, Any]], selected: Sequence[str]) -> list[Dict[str, Any]]:
    if not selected:
        return [by_id[key] for key in EXPECTED_RUNS]
    unknown = sorted(set(selected) - set(by_id))
    require(not unknown, f"unknown run id(s): {unknown}")
    require(len(selected) == len(set(selected)), "duplicate --run-id")
    return [by_id[key] for key in selected]


def assert_outputs_absent(runs: Iterable[Dict[str, Any]]) -> None:
    for run in runs:
        for key in ("output_dir", "optimizer_log", "stdout_log", "status_file"):
            path = relative_extension_path(run[key], f"{run['run_id']}.{key}")
            require(not path.exists(),
                    f"REFUSING: prior output/log/status exists for {run['run_id']}: {path}")


def gpu_snapshot(gpu: int, idle: Dict[str, Any]) -> Dict[str, int]:
    query = subprocess.run(
        ["nvidia-smi", "-i", str(gpu),
         "--query-gpu=memory.used,utilization.gpu",
         "--format=csv,noheader,nounits"],
        check=False, capture_output=True, text=True,
    )
    require(query.returncode == 0,
            f"nvidia-smi failed for GPU {gpu}: {query.stderr.strip()}")
    try:
        memory, utilization = [int(part.strip())
                               for part in query.stdout.strip().split(",")]
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"cannot parse GPU {gpu} status: {query.stdout!r}") from exc
    process_query = subprocess.run(
        ["nvidia-smi", "-i", str(gpu), "--query-compute-apps=pid",
         "--format=csv,noheader,nounits"],
        check=False, capture_output=True, text=True,
    )
    require(process_query.returncode == 0,
            f"cannot query compute PIDs on GPU {gpu}: {process_query.stderr.strip()}")
    pids = [int(token) for token in re.findall(r"\b\d+\b", process_query.stdout)]
    require(not pids, f"GPU {gpu} has compute process(es): {pids}")
    require(memory <= idle["maximum_memory_used_mib"],
            f"GPU {gpu} memory is not idle: {memory} MiB")
    require(utilization <= idle["maximum_utilization_percent"],
            f"GPU {gpu} utilization is not idle: {utilization}%")
    return {"gpu": gpu, "memory_used_mib": memory,
            "utilization_percent": utilization, "compute_pids": pids}


def environment_preflight(config: Dict[str, Any], runs: Iterable[Dict[str, Any]]) -> list[dict]:
    remote = config["remote_execution"]
    require(REPO.resolve().as_posix() == remote["repo_root"],
            f"must run from the exact L40 repository {remote['repo_root']}; got {REPO}")
    require(platform.node().split(".")[0] == remote["hostname"],
            f"wrong host: expected {remote['hostname']}, got {platform.node()}")
    require(Path(sys.executable).resolve().as_posix() == remote["python"],
            f"wrong Python: expected {remote['python']}, got {sys.executable}")
    require(os.environ.get("PYTHONNOUSERSITE") == "1",
            "PYTHONNOUSERSITE must equal 1 before preflight (user-site packages change the stack)")
    for executable in ("nvidia-smi", "iverilog", "vvp", "flock"):
        require(shutil.which(executable) is not None,
                f"required executable is not on PATH: {executable}")
    free = shutil.disk_usage(REPO).free
    minimum = remote["minimum_repo_filesystem_free_gib"] * (1 << 30)
    require(free >= minimum,
            f"insufficient free space: {free / (1 << 30):.1f} GiB; need {minimum / (1 << 30):.1f}")
    canary = subprocess.run(
        [sys.executable, "-c",
         "import json,sys,torch,transformers,peft,accelerate,numpy,scipy,sklearn,joblib; "
         "assert torch.cuda.is_available(); "
         "import oracle, gen_accelerator_catalog as G; "
         "r=oracle.score(G.fir_ref('fir8_8b', G.fir_coeffs(8)), 'fir8_8b', n=64); "
         "assert r['correct'], r; "
         "print(json.dumps({'python':sys.version.split()[0],"
         "'torch':torch.__version__,'transformers':transformers.__version__,"
         "'peft':peft.__version__,'accelerate':accelerate.__version__,"
         "'numpy':numpy.__version__,'scipy':scipy.__version__,"
         "'scikit_learn':sklearn.__version__,'joblib':joblib.__version__}))"],
        cwd=REPO, check=False, capture_output=True, text=True,
    )
    require(canary.returncode == 0,
            f"CUDA/oracle canary failed: {(canary.stderr or canary.stdout).strip()}")
    try:
        observed_versions = json.loads(canary.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError) as exc:
        raise ValidationError(f"cannot parse environment canary: {canary.stdout!r}") from exc
    required_versions = dict(remote["required_environment"])
    required_versions.pop("PYTHONNOUSERSITE")
    expected_iverilog = required_versions.pop("iverilog")
    require(observed_versions == required_versions,
            f"environment version drift: expected {required_versions}, got {observed_versions}")
    iverilog = subprocess.run(["iverilog", "-V"], check=False,
                              capture_output=True, text=True)
    require(iverilog.returncode == 0 and
            f"Icarus Verilog version {expected_iverilog}" in
            (iverilog.stdout + iverilog.stderr),
            f"iverilog version drift: {(iverilog.stdout + iverilog.stderr).splitlines()[:1]}")
    idle = remote["gpu_idle"]
    return [gpu_snapshot(int(run["physical_gpu"]), idle) for run in runs]


def expected_command(config: Dict[str, Any], run: Dict[str, Any]) -> list[str]:
    remote, protocol = config["remote_execution"], config["training_protocol"]
    command = [
        remote["python"], "-u", "grpo_oracle.py",
        "--base", remote["base_model"], "--sft", remote["sft_adapter"],
        "--reward", run["reward"],
    ]
    if run["reward"] == "rf_struct":
        command += ["--rf", str(run["reward_artifact"])]
    command += [
        "--dtype", "fp16", "--seed", str(run["training_seed"]),
        "--steps", str(run["max_attempted_groups"]),
        "--max-updates", str(protocol["target_nonflat_updates"]),
        "--max-groups", str(run["max_attempted_groups"]),
        "--save-at-updates", ",".join(map(str, protocol["checkpoints_at_updates"])),
        "--group", str(protocol["group_size"]),
        "--gen-batch", str(protocol["generation_batch"]),
        "--temp", str(protocol["temperature"]),
        "--max-tokens", str(protocol["max_tokens"]),
        "--lr", str(protocol["learning_rate"]),
        "--kl_coef", str(protocol["kl_coefficient"]),
        "--incorrect-reward", str(protocol["incorrect_reward"]),
        "--out", run["output_dir"], "--log", run["optimizer_log"],
    ]
    return command


def audit_jsonl(path: Path, group_log: bool) -> Dict[str, Any]:
    require(path.is_file(), f"missing JSONL: {path}")
    groups: Dict[int, list] = {}
    updates: Dict[int, int] = {}
    rows = 0
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise ValidationError(f"malformed JSON at {path}:{line_number}") from exc
            require(isinstance(row, dict), f"non-object JSON at {path}:{line_number}")
            rows += 1
            if not group_log:
                update = row.get("update")
                require(isinstance(update, int) and update > 0,
                        f"bad update at {path}:{line_number}")
                require(update not in updates, f"duplicate update {update} in {path}")
                updates[update] = line_number
                continue
            group = row.get("group_index")
            require(isinstance(group, int) and group > 0,
                    f"bad group at {path}:{line_number}")
            groups.setdefault(group, []).append(row)
    if not group_log:
        require(set(updates) == set(range(1, TARGET_UPDATES + 1)),
                f"{path} does not contain exactly optimizer updates 1..{TARGET_UPDATES}")
        return {"path": str(path), "sha256": sha256_file(path),
                "rows": rows, "updates": len(updates)}

    require(groups, f"empty group log: {path}")
    require(set(groups) == set(range(1, len(groups) + 1)),
            f"group indices are not consecutive in {path}")
    flat_groups = 0
    for group_index, group_rows in groups.items():
        require(len(group_rows) == 8,
                f"group {group_index} in {path} has {len(group_rows)} candidates")
        require({row.get("cand") for row in group_rows} == set(range(8)),
                f"group {group_index} has wrong candidate indices")
        require({row.get("step") for row in group_rows} == {group_index - 1},
                f"group {group_index} has wrong step index")
        require(len({row.get("design") for row in group_rows}) == 1,
                f"group {group_index} mixes designs")
        flat_values = {row.get("flat") for row in group_rows}
        update_values = {row.get("update") for row in group_rows}
        require(len(flat_values) == 1 and len(update_values) == 1,
                f"group {group_index} is internally inconsistent")
        flat, update = next(iter(flat_values)), next(iter(update_values))
        if flat is True:
            flat_groups += 1
            require(update is None, f"flat group {group_index} has an update")
        elif flat is False:
            require(isinstance(update, int) and update > 0,
                    f"non-flat group {group_index} has no update")
            require(update not in updates,
                    f"update {update} appears in multiple groups")
            updates[update] = group_index
        else:
            raise ValidationError(f"group {group_index} has no Boolean flat flag")
    require(set(updates) == set(range(1, TARGET_UPDATES + 1)),
            f"{path} does not contain exactly updates 1..{TARGET_UPDATES}")
    return {"path": str(path), "sha256": sha256_file(path), "rows": rows,
            "groups": len(groups), "updates": len(updates),
            "flat_groups": flat_groups}


def audit_run(config: Dict[str, Any], run: Dict[str, Any]) -> Dict[str, Any]:
    run_id = run["run_id"]
    output = relative_extension_path(run["output_dir"], f"{run_id}.output_dir")
    optimizer_log = relative_extension_path(run["optimizer_log"], f"{run_id}.optimizer_log")
    status_path = relative_extension_path(run["status_file"], f"{run_id}.status_file")
    stdout_path = relative_extension_path(run["stdout_log"], f"{run_id}.stdout_log")
    require(output.is_dir(), f"missing run directory: {output}")
    require(stdout_path.is_file() and stdout_path.stat().st_size > 0,
            f"missing/empty stdout log: {stdout_path}")
    status = read_json(status_path)
    require(status.get("schema_version") == 1 and status.get("study_id") == config["study_id"],
            f"bad status identity for {run_id}")
    require(status.get("run_id") == run_id and status.get("state") == "COMPLETE",
            f"{run_id} status is not COMPLETE")
    require(status.get("exit_code") == 0, f"{run_id} exit code is not zero")
    require(status.get("physical_gpu") == run["physical_gpu"],
            f"{run_id} status GPU changed")
    require(status.get("config_sha256") == sha256_file(HERE / "config.json"),
            f"{run_id} status config hash changed")
    require(status.get("validator_sha256") == sha256_file(HERE / "validate.py"),
            f"{run_id} status validator hash changed")
    require(status.get("launcher_sha256") == sha256_file(HERE / "launch.sh"),
            f"{run_id} status launcher hash changed")
    require(status.get("argv") == expected_command(config, run),
            f"{run_id} executed argv differs from frozen command")

    run_config = read_json(output / "run_config.json")
    summary = read_json(output / "run_summary.json")
    exact_config = {
        "reward": run["reward"], "seed": run["training_seed"],
        "group": 8, "temp": 1.0, "max_tokens": 1536, "lr": 1e-05,
        "kl_coef": 0.1, "incorrect_reward": 0.0,
        "steps": run["max_attempted_groups"], "max_updates": TARGET_UPDATES,
        "max_groups": run["max_attempted_groups"],
        "save_at_updates": CHECKPOINTS, "dtype": "torch.float16",
        "grad_clip": 1.0, "optimizer": "AdamW",
        "optimizer_defaults": {"betas": [0.9, 0.999], "eps": 1e-08,
                               "weight_decay": 0.01},
        "base": config["remote_execution"]["base_model"],
        "sft": str((REPO / config["remote_execution"]["sft_adapter"]).resolve()),
        "crash_policy": "discard and rerun from step 0; never resume or merge",
    }
    for key, expected in exact_config.items():
        require(run_config.get(key) == expected,
                f"{run_id} run_config.{key}: expected {expected!r}, got {run_config.get(key)!r}")
    if run["reward"] == "rf_struct":
        require(run_config.get("reward_source") == str((REPO / "rf_struct.joblib").resolve()),
                f"{run_id} RF reward source changed")
        rf_item = next(item for item in config["frozen_dependencies"]["items"]
                       if item["path"] == "rf_struct.joblib")
        require(run_config.get("reward_sha256") ==
                rf_item["legacy_run_config_lf_normalized_binary_sha256"],
                f"{run_id} RF reward hash changed")
    else:
        require(run_config.get("reward_source") ==
                "constant 1.0 (correctness-only control)",
                f"{run_id} correctness reward source changed")
        require(run_config.get("reward_sha256") is None,
                f"{run_id} correctness reward unexpectedly has an artifact hash")
    item_hashes = {item["path"]: item["sha256"]
                   for item in config["frozen_dependencies"]["items"]}
    expected_code = {name: item_hashes[name] for name in (
        "grpo_oracle.py", "oracle.py", "canonicalize.py",
        "gen_sft_corpus.py", "gen_accelerator_catalog.py")}
    require(run_config.get("code_sha256") == expected_code,
            f"{run_id} recorded code hashes differ from frozen dependencies")
    require(isinstance(run_config.get("n_designs"), int) and run_config["n_designs"] > 0,
            f"{run_id} has no training designs")
    require(isinstance(run_config.get("designs"), list)
            and len(run_config["designs"]) == run_config["n_designs"]
            and len(set(run_config["designs"])) == run_config["n_designs"],
            f"{run_id} training-design list is malformed")

    require(summary.get("updates") == TARGET_UPDATES,
            f"{run_id} stopped at {summary.get('updates')} updates")
    require(summary.get("ended") == "target updates reached (276)",
            f"{run_id} ended unexpectedly: {summary.get('ended')!r}")
    require(summary.get("checkpoints") == CHECKPOINTS
            and summary.get("missed_checkpoints") == [],
            f"{run_id} checkpoint summary is incomplete")
    for checkpoint in CHECKPOINTS:
        directory = output / f"upd_{checkpoint}"
        require(directory.is_dir() and any(directory.iterdir()),
                f"missing/empty checkpoint {directory}")

    group = audit_jsonl(output / "group_log.jsonl", group_log=True)
    optimizer = audit_jsonl(optimizer_log, group_log=False)
    require(summary.get("attempted_groups") == group["groups"],
            f"{run_id} attempted-group count disagrees with group log")
    require(summary.get("flat_groups") == group["flat_groups"],
            f"{run_id} flat-group count disagrees with group log")
    require(group["groups"] <= run["max_attempted_groups"],
            f"{run_id} exceeded its frozen attempt ceiling")
    return {
        "run_id": run_id, "reward": run["reward"], "seed": run["training_seed"],
        "physical_gpu": run["physical_gpu"],
        "attempted_groups": group["groups"], "flat_groups": group["flat_groups"],
        "run_config_sha256": sha256_file(output / "run_config.json"),
        "run_summary_sha256": sha256_file(output / "run_summary.json"),
        "stdout_sha256": sha256_file(stdout_path), "group_log": group,
        "optimizer_log": optimizer, "status_sha256": sha256_file(status_path),
    }


def write_audit(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8", newline="\n")
    temporary.replace(path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--mode", choices=("config", "gate", "prelaunch", "completed"),
                        default="config")
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)
    try:
        config_path = Path(args.config).resolve()
        config = read_json(config_path)
        by_id = validate_config(config)
        runs = select_runs(by_id, args.run_id)
        payload: Dict[str, Any] = {
            "schema_version": 1, "study_id": config["study_id"],
            "mode": args.mode, "selected_runs": [run["run_id"] for run in runs],
            "config_path": str(config_path), "config_sha256": sha256_file(config_path),
        }
        if args.mode == "config":
            payload["dependencies"] = verify_dependencies(config, require_server=False)
        elif args.mode == "gate":
            payload["timing_gate"] = verify_timing_gate(config)
        elif args.mode == "prelaunch":
            payload["dependencies"] = verify_dependencies(config, require_server=True)
            payload["timing_gate"] = verify_timing_gate(config)
            assert_outputs_absent(runs)
            payload["gpu_snapshots"] = environment_preflight(config, runs)
        else:
            payload["dependencies"] = verify_dependencies(config, require_server=True)
            payload["timing_gate"] = verify_timing_gate(config)
            payload["runs"] = [audit_run(config, run) for run in runs]
            payload["complete"] = len(payload["runs"]) == len(runs)
            payload["interpretation"] = (
                "Prospective post-primary seed replication; do not pool these runs "
                "into the frozen Study 2 primary analysis.")
        if args.out:
            write_audit(Path(args.out), payload)
    except (ValidationError, OSError, subprocess.SubprocessError) as exc:
        print(f"seed extension validation error: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: {args.mode} validation for {', '.join(run['run_id'] for run in runs)}")
    if args.out:
        print(f"audit -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
