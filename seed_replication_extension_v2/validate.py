#!/usr/bin/env python3
"""Fail-closed validator for the V100 seed-replication amendment."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence


HERE = Path(__file__).resolve().parent
REPO = HERE.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from seed_replication_extension_v1 import validate as base  # noqa: E402


DEFAULT_CONFIG = HERE / "config.json"
PARENT_CONFIG_SHA256 = "3ae8f352b0cbaf92dbcacd0f15e2791c8c72ee588d51628e51554275985c80ff"
PARENT_PROTOCOL_SHA256 = "6257a08fa4138b5bf0cc22731e467886f4bafb732ac723ee6dc126313b6dc807"
EXPECTED_RUNS = {
    "rf_s3": ("repaired_rf", "rf_struct", 3, "v100a", "49ed1pm9lmiqe-0",
              "Tesla V100-SXM2-32GB", 0, 2000),
    "rf_s4": ("repaired_rf", "rf_struct", 4, "v100b", "8cqofmihc71pg-0",
              "Tesla V100S-PCIE-32GB", 0, 2000),
    "correctness_s2": ("correctness_only", "correctness", 2, "v100a",
                       "49ed1pm9lmiqe-0", "Tesla V100-SXM2-32GB", 1, 15000),
    "correctness_s3": ("correctness_only", "correctness", 3, "v100b",
                       "8cqofmihc71pg-0", "Tesla V100S-PCIE-32GB", 1, 15000),
}


def require(condition: bool, message: str) -> None:
    base.require(condition, message)


def raw_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_parent(config: Dict[str, Any]) -> Dict[str, Any]:
    parent = config.get("parent_protocol", {})
    expected = {
        "config_path": "seed_replication_extension_v1/config.json",
        "config_sha256_raw": PARENT_CONFIG_SHA256,
        "protocol_path": "seed_replication_extension_v1/PROTOCOL.md",
        "protocol_sha256_raw": PARENT_PROTOCOL_SHA256,
    }
    for key, value in expected.items():
        require(parent.get(key) == value,
                f"parent_protocol.{key}: expected {value!r}, got {parent.get(key)!r}")
    config_path = REPO / parent["config_path"]
    protocol_path = REPO / parent["protocol_path"]
    require(config_path.is_file() and protocol_path.is_file(),
            "parent V1 protocol files are missing")
    require(raw_sha256(config_path) == PARENT_CONFIG_SHA256,
            "parent V1 config raw hash drift")
    require(raw_sha256(protocol_path) == PARENT_PROTOCOL_SHA256,
            "parent V1 protocol raw hash drift")
    value = base.read_json(config_path)
    require(value.get("study_id") == "seed_replication_extension_v1",
            "wrong parent study identity")
    require(value.get("status") == "prepared_not_launched",
            "parent V1 status changed")
    return value


def validate_config(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    require(config.get("schema_version") == 2, "config schema_version is not 2")
    require(config.get("study_id") == "seed_replication_extension_v2",
            "wrong config study_id")
    require(config.get("status") == "prepared_not_launched",
            "V2 config status must remain prepared_not_launched")
    parent = load_parent(config)

    # Materialize unchanged V1 contracts in memory. The raw parent hash makes
    # this stronger than copying those fields and risking silent divergence.
    for key in ("separation_from_prior_studies", "training_protocol",
                "prospective_evaluation_contract_not_launched_here"):
        config[key] = copy.deepcopy(parent[key])
    frozen = copy.deepcopy(parent["frozen_dependencies"])
    for item in frozen["items"]:
        if item.get("path") == "/home/adam/mas/mas/rtlcoder":
            item["path"] = "/zeng_gk/Amine/mas/rtlcoder"
    config["frozen_dependencies"] = frozen

    remote = config.get("remote_execution", {})
    exact_remote = {
        "repo_root": "/zeng_gk/Amine/mas/fpga-v100-v2",
        "allowed_parent": "/zeng_gk/Amine/mas",
        "python": "/zeng_gk/Amine/mas/env_mas/bin/python",
        "environment_bin": "/zeng_gk/Amine/mas/env_mas/bin",
        "base_model": "/zeng_gk/Amine/mas/rtlcoder",
        "sft_adapter": "sft_v6c_out",
        "minimum_repo_filesystem_free_gib": 25,
    }
    for key, value in exact_remote.items():
        require(remote.get(key) == value,
                f"remote_execution.{key}: expected {value!r}, got {remote.get(key)!r}")
    require(remote.get("hosts") == {
        "v100a": {"hostname": "49ed1pm9lmiqe-0",
                  "gpu_model": "Tesla V100-SXM2-32GB",
                  "allowed_physical_gpus": [0, 1]},
        "v100b": {"hostname": "8cqofmihc71pg-0",
                  "gpu_model": "Tesla V100S-PCIE-32GB",
                  "allowed_physical_gpus": [0, 1]},
    }, "V100 host identities or GPU allocation changed")
    require(remote.get("required_environment") == {
        "PYTHONNOUSERSITE": "1", "python": "3.10.20",
        "torch": "2.4.1+cu121", "transformers": "4.46.3",
        "peft": "0.13.2", "accelerate": "1.0.1", "numpy": "2.2.6",
        "scipy": "1.15.3", "scikit_learn": "1.7.2",
        "joblib": "1.5.3", "iverilog": "12.0",
    }, "required V100 environment versions changed")
    require(remote.get("gpu_idle") == {
        "maximum_memory_used_mib": 128,
        "maximum_utilization_percent": 1,
        "require_no_compute_pids": True,
        "checks_immediately_before_launch": 2,
        "seconds_between_checks": 2,
    }, "GPU-idle contract changed")

    gate = config.get("launch_prerequisites", {}).get("timing_gate", {})
    exact_gate = {
        "result_path": "timing_closure_candidate_v7/results/pilot_gate.json",
        "candidate_manifest_path": "timing_closure_candidate_v7/manifest.json",
        "candidate_manifest_sha256_path": "timing_closure_candidate_v7/manifest.sha256",
        "expected_candidate_package_sha256": "6d2512c8d256dde29eb7c45754bf4e3e42a89a2e6ef23d121af1e9e768496049",
        "v1_manifest_path": "timing_closure_gate_v1/manifest.json",
        "expected_v1_manifest_sha256": "2e0674f96c57be3864a6fab7683b0edc76f732762f78547d5e6a3e8efc17e194",
        "schema_version": 1, "study_id": "timing_closure_candidate_v7",
        "scope": "pilot_10", "vivado_version": "2026.1",
        "expected_candidates": 10, "required_verdict": "PASS",
        "required_criteria": ["complete_and_constrained", "spearman_ge_0_90",
                              "median_smape_le_0_15", "paired_direction"],
    }
    require(gate == exact_gate, "timing-gate contract changed")

    by_id: Dict[str, Dict[str, Any]] = {}
    paths = set()
    runs = config.get("runs")
    require(isinstance(runs, list) and len(runs) == 4,
            "config must contain exactly four runs")
    for run in runs:
        require(isinstance(run, dict), "a run entry is not an object")
        run_id = run.get("run_id")
        require(run_id in EXPECTED_RUNS and run_id not in by_id,
                f"unexpected or duplicate run_id {run_id!r}")
        condition, reward, seed, alias, host, model, gpu, ceiling = EXPECTED_RUNS[run_id]
        exact = {
            "condition": condition, "reward": reward,
            "reward_artifact": "rf_struct.joblib" if reward == "rf_struct" else None,
            "training_seed": seed, "ssh_alias": alias, "hostname": host,
            "gpu_model": model, "physical_gpu": gpu,
            "max_attempted_groups": ceiling,
            "output_dir": f"{HERE.name}/runs/grpo_{run_id}",
            "optimizer_log": f"{HERE.name}/logs/{run_id}.optimizer.jsonl",
            "stdout_log": f"{HERE.name}/logs/{run_id}.stdout.log",
            "status_file": f"{HERE.name}/status/{run_id}.status.json",
        }
        for key, value in exact.items():
            require(run.get(key) == value,
                    f"{run_id}.{key}: expected {value!r}, got {run.get(key)!r}")
        for key in ("output_dir", "optimizer_log", "stdout_log", "status_file"):
            path = base.relative_extension_path(run[key], f"{run_id}.{key}")
            require(path not in paths, f"duplicate output path {path}")
            paths.add(path)
        by_id[run_id] = run
    require(set(by_id) == set(EXPECTED_RUNS), "the frozen run set changed")
    return by_id


def verify_timing_gate(config: Dict[str, Any]) -> Dict[str, Any]:
    gate = config["launch_prerequisites"]["timing_gate"]
    paths = {key: REPO / gate[key] for key in (
        "result_path", "candidate_manifest_path",
        "candidate_manifest_sha256_path", "v1_manifest_path")}
    for path in paths.values():
        require(path.is_file(), f"timing gate prerequisite missing: {path}")
    tokens = paths["candidate_manifest_sha256_path"].read_text(
        encoding="ascii").split()
    require(tokens and tokens[0] == gate["expected_candidate_package_sha256"],
            "V7 candidate manifest digest file differs from V2 pin")
    require(raw_sha256(paths["candidate_manifest_path"]) ==
            gate["expected_candidate_package_sha256"],
            "V7 candidate manifest content differs from V2 pin")
    require(raw_sha256(paths["v1_manifest_path"]) ==
            gate["expected_v1_manifest_sha256"],
            "V1 candidate manifest differs from V2 pin")

    result = base.read_json(paths["result_path"])
    exact = {
        "schema_version": gate["schema_version"],
        "study_id": gate["study_id"], "scope": gate["scope"],
        "vivado_version": gate["vivado_version"],
        "v1_manifest_sha256": gate["expected_v1_manifest_sha256"],
        "candidate_package_sha256": gate["expected_candidate_package_sha256"],
        "expected_candidates": gate["expected_candidates"],
        "completed_candidates": gate["expected_candidates"],
        "verdict": gate["required_verdict"],
    }
    for key, value in exact.items():
        require(result.get(key) == value,
                f"timing result {key}: expected {value!r}, got {result.get(key)!r}")
    criteria = result.get("criteria")
    require(isinstance(criteria, dict), "timing result lacks criteria")
    for key in gate["required_criteria"]:
        require(criteria.get(key) is True, f"timing criterion failed: {key}")
    require(result.get("failures") == [], "timing gate reports failures")
    metrics = result.get("metrics")
    require(isinstance(metrics, dict), "timing gate lacks metrics")
    for key in ("spearman_rho", "median_smape", "rf_minus_sft_mean_mhz",
                "sign_reversals", "non_tied_pairs"):
        require(metrics.get(key) is not None, f"timing metric missing/null: {key}")
    sources = result.get("generated_from")
    require(isinstance(sources, list) and sources,
            "timing result lacks generated-from provenance")
    verified = []
    for source in sources:
        require(isinstance(source, dict), "malformed generated-from record")
        rel, expected = source.get("path"), source.get("sha256")
        require(isinstance(rel, str) and isinstance(expected, str),
                "malformed generated-from identity")
        candidate = Path(rel)
        candidates = ([candidate] if candidate.is_absolute() else
                      [REPO / candidate, paths["result_path"].parent / candidate,
                       paths["result_path"].parent.parent / candidate])
        found = next((path for path in candidates if path.is_file()), None)
        require(found is not None, f"cannot resolve generated-from path {rel}")
        require(raw_sha256(found) == expected,
                f"generated-from hash mismatch: {found}")
        verified.append({"path": str(found), "sha256": expected})
    return {"path": str(paths["result_path"]),
            "sha256": raw_sha256(paths["result_path"]),
            "metrics": metrics, "generated_from": verified}


def current_host(config: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    hostname = platform.node().split(".")[0]
    matches = [(alias, spec) for alias, spec in
               config["remote_execution"]["hosts"].items()
               if spec["hostname"] == hostname]
    require(len(matches) == 1, f"undeclared execution host: {hostname}")
    return matches[0]


def environment_preflight(config: Dict[str, Any],
                          runs: Iterable[Dict[str, Any]]) -> list[dict]:
    selected = list(runs)
    remote = config["remote_execution"]
    require(REPO.resolve().as_posix() == remote["repo_root"],
            f"wrong repository path: {REPO}")
    require(Path(sys.executable).resolve().as_posix() == remote["python"],
            f"wrong Python: {sys.executable}")
    require(os.environ.get("PYTHONNOUSERSITE") == "1",
            "PYTHONNOUSERSITE must equal 1")
    alias, host = current_host(config)
    require(selected and all(run["ssh_alias"] == alias for run in selected),
            f"selected run is not assigned to this host ({alias})")
    for executable in ("nvidia-smi", "iverilog", "vvp", "flock"):
        require(shutil.which(executable) is not None,
                f"required executable is not on PATH: {executable}")
    free = shutil.disk_usage(REPO).free
    minimum = remote["minimum_repo_filesystem_free_gib"] * (1 << 30)
    require(free >= minimum,
            f"insufficient free space: {free / (1 << 30):.1f} GiB")
    iv = subprocess.run(["iverilog", "-V"], check=False,
                        capture_output=True, text=True)
    require(iv.returncode == 0 and "Icarus Verilog version 12.0" in
            (iv.stdout + iv.stderr), "Icarus Verilog is not version 12.0")

    required = dict(remote["required_environment"])
    required.pop("PYTHONNOUSERSITE")
    required.pop("iverilog")
    records = []
    for run in selected:
        before = base.gpu_snapshot(run["physical_gpu"], remote["gpu_idle"])
        env = dict(os.environ)
        env["CUDA_VISIBLE_DEVICES"] = str(run["physical_gpu"])
        canary = subprocess.run(
            [sys.executable, "-c",
             "import json,sys,torch,transformers,peft,accelerate,numpy,scipy,sklearn,joblib; "
             "assert torch.cuda.is_available(); x=torch.arange(4096,device='cuda'); "
             "assert int(x.sum())==8386560; "
             "import oracle,gen_accelerator_catalog as G; "
             "r=oracle.score(G.fir_ref('fir8_8b',G.fir_coeffs(8)),'fir8_8b',n=64); "
             "assert r['correct'],r; print(json.dumps({"
             "'python':sys.version.split()[0],'torch':torch.__version__,"
             "'transformers':transformers.__version__,'peft':peft.__version__,"
             "'accelerate':accelerate.__version__,'numpy':numpy.__version__,"
             "'scipy':scipy.__version__,'scikit_learn':sklearn.__version__,"
             "'joblib':joblib.__version__,'gpu':torch.cuda.get_device_name(0)}))"],
            cwd=REPO, env=env, check=False, capture_output=True, text=True,
        )
        require(canary.returncode == 0,
                f"GPU {run['physical_gpu']} CUDA/oracle canary failed: "
                f"{(canary.stderr or canary.stdout).strip()}")
        observed = json.loads(canary.stdout.strip().splitlines()[-1])
        gpu_name = observed.pop("gpu")
        require(observed == required,
                f"environment version drift: expected {required}, got {observed}")
        require(gpu_name == host["gpu_model"] == run["gpu_model"],
                f"GPU model mismatch: {gpu_name}")
        after = base.gpu_snapshot(run["physical_gpu"], remote["gpu_idle"])
        driver = subprocess.run(
            ["nvidia-smi", "-i", str(run["physical_gpu"]),
             "--query-gpu=driver_version", "--format=csv,noheader"],
            check=True, capture_output=True, text=True).stdout.strip()
        records.append({"run_id": run["run_id"], "ssh_alias": alias,
                        "hostname": host["hostname"],
                        "physical_gpu": run["physical_gpu"],
                        "gpu_model": gpu_name, "driver": driver,
                        "before": before, "after": after,
                        "cuda_oracle_canary": "PASS"})
    return records


_base_audit_run = base.audit_run


def audit_run(config: Dict[str, Any], run: Dict[str, Any]) -> Dict[str, Any]:
    record = _base_audit_run(config, run)
    status = base.read_json(base.relative_extension_path(
        run["status_file"], f"{run['run_id']}.status_file"))
    require(status.get("hostname") == run["hostname"],
            f"{run['run_id']} status hostname changed")
    require(status.get("gpu_model") == run["gpu_model"],
            f"{run['run_id']} status GPU model changed")
    record.update({"ssh_alias": run["ssh_alias"],
                   "hostname": run["hostname"],
                   "gpu_model": run["gpu_model"]})
    return record


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--mode", choices=("config", "gate", "host-ready",
                                            "prelaunch", "completed"),
                        default="config")
    parser.add_argument("--run-id", action="append", default=[])
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)
    try:
        config_path = Path(args.config).resolve()
        config = base.read_json(config_path)
        by_id = validate_config(config)
        runs = base.select_runs(by_id, args.run_id)
        payload: Dict[str, Any] = {
            "schema_version": 2, "study_id": config["study_id"],
            "mode": args.mode, "selected_runs": [r["run_id"] for r in runs],
            "config_path": str(config_path),
            "config_sha256": base.sha256_file(config_path),
        }
        if args.mode == "config":
            payload["dependencies"] = base.verify_dependencies(
                config, require_server=False)
        elif args.mode == "gate":
            payload["timing_gate"] = verify_timing_gate(config)
        elif args.mode == "host-ready":
            payload["dependencies"] = base.verify_dependencies(
                config, require_server=True)
            base.assert_outputs_absent(runs)
            payload["gpu_canaries"] = environment_preflight(config, runs)
        elif args.mode == "prelaunch":
            payload["dependencies"] = base.verify_dependencies(
                config, require_server=True)
            payload["timing_gate"] = verify_timing_gate(config)
            base.assert_outputs_absent(runs)
            payload["gpu_canaries"] = environment_preflight(config, runs)
        else:
            payload["dependencies"] = base.verify_dependencies(
                config, require_server=True)
            payload["timing_gate"] = verify_timing_gate(config)
            payload["runs"] = [audit_run(config, run) for run in runs]
            payload["complete"] = len(payload["runs"]) == len(runs)
        if args.out:
            base.write_audit(Path(args.out), payload)
    except (base.ValidationError, OSError, ValueError,
            subprocess.SubprocessError) as exc:
        print(f"seed extension V2 validation error: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: {args.mode} validation for "
          f"{', '.join(run['run_id'] for run in runs)}")
    if args.out:
        print(f"audit -> {args.out}")
    return 0


# Repoint inherited generic helpers to the V2 package before main executes.
base.HERE = HERE
base.REPO = REPO
base.DEFAULT_CONFIG = DEFAULT_CONFIG
base.EXPECTED_RUNS = {
    key: (condition, reward, seed, gpu, ceiling,
          f"runs/grpo_{key}", f"logs/{key}.optimizer.jsonl",
          f"logs/{key}.stdout.log", f"status/{key}.status.json")
    for key, (condition, reward, seed, _alias, _host, _model, gpu, ceiling)
    in EXPECTED_RUNS.items()
}


if __name__ == "__main__":
    raise SystemExit(main())
