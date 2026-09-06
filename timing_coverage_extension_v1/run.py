"""Frozen exhaustive primary-candidate coverage replay; immutable old results."""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from eval_sealed import sha256_file
from timing_closure_candidate_v7.run_candidates import dependency_guard
from timing_closure_candidate_v7.common import BASELINE, verify_v7_pass


def write(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")


def freeze():
    if (HERE / "results").exists():
        raise RuntimeError("Cannot freeze after execution")
    files = ["timing_coverage_extension_v1/run.py", "timing_coverage_extension_v1/PROTOCOL.md",
             "timing_path_audit_v1/replay.tcl", "ppa_synth.tcl", "sealed_split.json",
             "timing_closure_candidate_v7/run_candidates.py", "timing_closure_candidate_v7/common.py",
             "timing_closure_gate_v7/stability_common.py", "timing_closure_gate_v4/stability_common.py",
             "timing_closure_gate_v7/dependency_baseline.json"]
    candidates = []
    for directory in ("sealed_sft", "sealed_rf_s1", "sealed_rf_s2"):
        base = "rtl/" + directory + "/"
        manifest = json.loads((ROOT / (base + "fmax_manifest.json")).read_text())
        files.extend(base + name for name in ("fmax_manifest.json", "holdout_summary.json", "ppa.jsonl"))
        for module, meta in sorted(manifest.items()):
            path = base + module + ".sv"
            if sha256_file(str(ROOT / path)) != meta["emitted_sha256"]:
                raise RuntimeError("RTL differs from original manifest")
            files.append(path)
            candidates.append(dict(module=module, path=path, **meta))
    if len(candidates) != 202:
        raise RuntimeError("Unexpected candidate universe")
    write(HERE / "freeze.json", {"frozen_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "post-primary exhaustive SFT/RF cross-version coverage diagnostic",
        "candidates": candidates, "files_sha256_lf": {p: sha256_file(str(ROOT / p)) for p in files}})


def verify():
    frozen = json.loads((HERE / "freeze.json").read_text())
    for path, expected in frozen["files_sha256_lf"].items():
        if sha256_file(str(ROOT / path)) != expected:
            raise RuntimeError("Frozen input changed: " + path)
    return frozen


def run(scratch):
    frozen = verify()
    verify_v7_pass()
    baseline = json.loads(BASELINE.read_text())
    results = HERE / "results"
    results.mkdir(exist_ok=True)
    scratch.mkdir(exist_ok=True)
    freeze_hash = sha256_file(str(HERE / "freeze.json"))
    for index, candidate in enumerate(frozen["candidates"], 1):
        directory = results / candidate["module"]
        final = directory / "completion.json"
        if final.exists():
            completed = json.loads(final.read_text())
            if completed["freeze_sha256_lf"] != freeze_hash:
                raise RuntimeError("Stale completion")
            for path, expected in completed["artifact_hashes"].items():
                if sha256_file(str(directory / path)) != expected:
                    raise RuntimeError("Completed artifact changed")
            continue
        directory.mkdir(exist_ok=False)
        print(f"[{index}/202] {candidate['module']}", flush=True)
        trials = []
        for attempt in range(2):
            trial = directory / f"attempt_{attempt}"
            trial.mkdir()
            work = scratch / f"c{index:03d}a{attempt}" / "w"
            temp = work.parent / "t"
            work.mkdir(parents=True, exist_ok=False)
            temp.mkdir()
            reports = trial / "reports"
            reports.mkdir()
            before = dependency_guard(baseline)
            if not before[0]:
                write(trial / "dependency_failure.json", {"before": before})
                raise RuntimeError("Vivado dependency drift before launch")
            command = [r"C:\AMD\2026.1\Vivado\bin\vivado.bat", "-mode", "batch",
                "-nojournal", "-nolog", "-notrace", "-tempDir", str(temp), "-source",
                str(ROOT / "timing_path_audit_v1/replay.tcl"), "-tclargs",
                str(ROOT / candidate["path"]), candidate["module"], "clk", "5.0",
                str(trial / "historical_formula.json"), str(ROOT / "ppa_synth.tcl"), str(reports)]
            write(trial / "launch.json", {"command": command, "before": before,
                "started_utc": datetime.now(timezone.utc).isoformat(), "freeze_sha256_lf": freeze_hash})
            with (trial / "stdout.log").open("w") as out, (trial / "stderr.log").open("w") as err:
                process = subprocess.run(subprocess.list2cmdline(command), shell=True, cwd=work,
                    stdout=out, stderr=err, timeout=3600)
            after = dependency_guard(baseline)
            record = {"attempt": attempt, "returncode": process.returncode, "after": after,
                      "classification": "INCONCLUSIVE"}
            diagnostic = reports / "path_diagnostic.json"
            if process.returncode == 0 and diagnostic.exists() and after[0]:
                record["diagnostic"] = json.loads(diagnostic.read_text())
                report_status = (reports / "report_status.txt").read_text()
                if "catch_code=1" not in report_status and "catch_code=2" not in report_status:
                    record["classification"] = ("SETUP_PATH_PRESENT" if record["diagnostic"]["setup_path_count"] > 0
                        and record["diagnostic"]["clock_count"] > 0 else "INVALID_NO_SETUP_PATH")
            write(trial / "measurement.json", record)
            trials.append(record)
            if not after[0]:
                raise RuntimeError("Vivado dependency drift after launch")
            if record["classification"] != "INCONCLUSIVE":
                break
        completed = {"candidate": candidate, "freeze_sha256_lf": freeze_hash,
            "classification": trials[-1]["classification"], "trials": trials,
            "completed_utc": datetime.now(timezone.utc).isoformat(),
            "artifact_hashes": {p.relative_to(directory).as_posix(): sha256_file(str(p))
                for p in sorted(directory.rglob("*")) if p.is_file()}}
        write(final, completed)
        print("  " + completed["classification"], flush=True)
    print("COMPLETE: all 202 candidates; review every inconclusive/invalid result before analysis", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--scratch", type=Path)
    args = parser.parse_args()
    if args.freeze:
        freeze()
    elif args.check:
        print("PASS:", len(verify()["candidates"]), "frozen candidates")
    elif args.scratch:
        run(args.scratch)
    else:
        parser.error("Choose --freeze, --check, or --scratch")
