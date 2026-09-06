"""Freeze the complete SFT plus three-policy candidate universe before Vivado."""
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from eval_sealed import load_split, sha256_file
from seed_replication_evaluation_v1.launch import validate_output

POLICIES = {
    "sft": (ROOT / "rtl/sealed_sft", 48, 0),
    "rf_s3": (ROOT / "seed_replication_evaluation_v1/outputs/rf_s3", 24, 3),
    "rf_s4": (ROOT / "seed_replication_evaluation_v1/outputs/rf_s4", 24, 4),
    "correctness_s2": (ROOT / "seed_replication_evaluation_v1/outputs/correctness_s2", 48, 2),
}


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(value, out, indent=2)
        out.write("\n")


def main():
    if (HERE / "manifest.json").exists() or (HERE / "results").exists():
        raise RuntimeError("Physical package already frozen or started")
    split = load_split(str(ROOT / "sealed_split.json"))
    files = {}
    candidates = []
    for policy, (directory, n, training_seed) in POLICIES.items():
        if policy != "sft":
            validate_output(policy, directory, check_adapter=False)
        manifest_path = directory / "fmax_manifest.json"
        summary_path = directory / "holdout_summary.json"
        manifest = json.loads(manifest_path.read_text())
        summary = json.loads(summary_path.read_text())
        summary_key = policy if policy != "sft" else "sft"
        if set(summary[summary_key]) != {d["design"] for d in split}:
            raise RuntimeError("Incomplete design universe: " + policy)
        if any(row["n"] != n for row in summary[summary_key].values()):
            raise RuntimeError("Draw budget mismatch: " + policy)
        for path in (manifest_path, summary_path):
            files[path.relative_to(ROOT).as_posix()] = sha256_file(str(path))
        generation = directory / "generation_config.json"
        if generation.exists():
            files[generation.relative_to(ROOT).as_posix()] = sha256_file(str(generation))
        for module, row in sorted(manifest.items()):
            source = directory / (module + ".sv")
            if sha256_file(str(source)) != row["emitted_sha256"]:
                raise RuntimeError("Emitted source mismatch: " + module)
            if row["policy"] != policy or row["n"] != n or not (0 < row["count"] <= n):
                raise RuntimeError("Candidate metadata mismatch: " + module)
            rel = source.relative_to(ROOT).as_posix()
            files[rel] = sha256_file(str(source))
            candidates.append({"candidate_id": f"p{len(candidates)+1:03d}_{module}",
                "module": module, "materialized_path": rel, "emitted_sha256": row["emitted_sha256"],
                "policy": policy, "training_seed": training_seed, "design": row["design"],
                "family": row["family"], "regime": row["regime"], "count": row["count"],
                "n": n, "clock_port": "clk", "arm": policy})
    if len(candidates) != 302 or len({c["module"] for c in candidates}) != 302:
        raise RuntimeError("Expected exactly 302 distinct emitted candidates")
    dependencies = ["seed_replication_physical_v1/PROTOCOL.md",
        "seed_replication_physical_v1/prepare.py", "seed_replication_physical_v1/run.py",
        "seed_replication_physical_v1/analyze.py", "seed_replication_physical_v1/test_package.py",
        "timing_closure_gate_v1/closure_synth.tcl", "timing_closure_gate_v1/run_closure.py",
        "timing_closure_candidate_v7/run_candidates.py", "timing_closure_candidate_v7/common.py",
        "timing_closure_gate_v7/stability_common.py", "timing_closure_gate_v4/stability_common.py",
        "timing_closure_gate_v7/dependency_baseline.json", "sealed_split.json"]
    for rel in dependencies:
        files[rel] = sha256_file(str(ROOT / rel))
    write_new(HERE / "manifest.json", {"schema_version": 1,
        "study_id": "seed_replication_physical_v1", "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "status": "frozen_before_first_physical_measurement", "vivado_version": "2026.1",
        "part": "xc7z020clg400-1", "n_designs": 20, "n_candidates": 302,
        "policies": {p: {"draws_per_design": n, "training_seed": s,
            "emitted_candidates": sum(c["policy"] == p for c in candidates)}
            for p, (_, n, s) in POLICIES.items()}, "candidates": candidates, "files_sha256_lf": files})
    print("Frozen 302 candidates before physical measurement")


if __name__ == "__main__":
    main()
