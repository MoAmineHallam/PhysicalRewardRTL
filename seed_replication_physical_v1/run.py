"""Run frozen V7 period closure for every additional-seed endpoint candidate."""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from eval_sealed import sha256_file
from timing_closure_candidate_v7.run_candidates import TrialRunnerV7
from timing_closure_candidate_v7.common import BASELINE, atomic_json, verify_v7_pass
from timing_closure_gate_v1 import run_closure as v1run


def verify_manifest():
    manifest = json.loads((HERE / "manifest.json").read_text())
    if manifest.get("study_id") != "seed_replication_physical_v1" or manifest.get("n_candidates") != 302:
        raise RuntimeError("Unexpected physical manifest")
    for rel, expected in manifest["files_sha256_lf"].items():
        if sha256_file(str(ROOT / rel)) != expected:
            raise RuntimeError("Frozen dependency changed: " + rel)
    for row in manifest["candidates"]:
        if sha256_file(str(ROOT / row["materialized_path"])) != row["emitted_sha256"]:
            raise RuntimeError("Candidate changed: " + row["module"])
    return manifest, sha256_file(str(HERE / "manifest.json"))


def completed_valid(path, identity):
    value = json.loads(path.read_text())
    if value.get("physical_manifest_sha256_lf") != identity:
        raise RuntimeError("Stale result identity: " + str(path))
    return value


def run(scratch):
    manifest, identity = verify_manifest()
    verify_v7_pass()
    results = HERE / "results"
    results.mkdir(exist_ok=True)
    scratch.mkdir(exist_ok=True)
    for index, frozen in enumerate(manifest["candidates"], 1):
        final_path = results / frozen["candidate_id"] / "closure_result.json"
        if final_path.exists():
            completed_valid(final_path, identity)
            continue
        print(f"[{index}/302] {frozen['module']}", flush=True)
        candidate = dict(frozen)
        runner = TrialRunnerV7(Path(r"C:\AMD\2026.1\Vivado\bin\vivado.bat"),
            candidate, index, identity, identity, results, scratch, retries=1)
        reference = runner.run(5.0, "reference_5ns")
        if not reference.get("valid_measurement"):
            value = {"schema_version": 1, "study_id": manifest["study_id"],
                "physical_manifest_sha256_lf": identity, "candidate": frozen,
                "status": "FAILED", "failure_reason": "permanent_invalid_reference_5ns",
                "closure_fmax_mhz": 0.0, "trial_count": len(runner.trials), "trials": runner.trials}
        else:
            wns = float(reference["vivado"]["wns_ns"])
            delay = 5.0 - wns
            if not math.isfinite(delay) or delay <= 0:
                raise RuntimeError("Invalid reference delay: " + frozen["module"])
            candidate.update(old_proxy_delay_ns=delay, old_fmax_mhz=1000.0/delay)
            raw = v1run.close_candidate(candidate, identity, runner)
            value = dict(raw)
            value.update(study_id=manifest["study_id"], physical_manifest_sha256_lf=identity,
                         candidate=frozen, reference_5ns=reference["vivado"])
            value.pop("manifest_sha256", None)
        atomic_json(final_path, value)
        print(f"  {value['status']}: {value['closure_fmax_mhz']:.6f} MHz", flush=True)
    print("COMPLETE: 302/302 physical candidates", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--scratch", type=Path)
    args = parser.parse_args()
    if args.check:
        print("PASS physical manifest", verify_manifest()[1])
    elif args.scratch:
        run(args.scratch)
    else:
        parser.error("Choose --check or --scratch")
