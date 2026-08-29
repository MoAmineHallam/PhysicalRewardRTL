#!/usr/bin/env python3
"""Run the V4 single-thread pre-candidate Vivado stability gate."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from .stability_common import (HERE, ROOT, VIVADO_ROOT, measurement_valid,
                                   raw_dependency_snapshot, read_json, sha256_file,
                                   write_json_new)
except ImportError:  # direct script execution
    from stability_common import (HERE, ROOT, VIVADO_ROOT, measurement_valid,
                                  raw_dependency_snapshot, read_json, sha256_file,
                                  write_json_new)


TCL = HERE / "closure_synth_single_thread.tcl"
PROBE = HERE / "stability_probe.sv"
BASELINE = HERE / "dependency_baseline.json"
DEFAULT_CAMPAIGN = HERE / "stability_campaign_001"
DEFAULT_SCRATCH_ROOT = Path(r"C:\VGT4S001")
RUNS = 20
GUARD_READ_PASSES = 3


def dependency_guard(baseline: dict) -> tuple[bool, dict, str | None]:
    try:
        actual = raw_dependency_snapshot(VIVADO_ROOT)
        for _ in range(1, GUARD_READ_PASSES):
            if raw_dependency_snapshot(VIVADO_ROOT) != actual:
                return False, actual, "dependency_guard_read_or_hash_failure"
    except Exception as exc:
        return False, {"error": str(exc)}, "dependency_guard_read_or_hash_failure"
    if actual != {key: baseline[key] for key in actual}:
        return False, actual, "dependency_guard_changed"
    return True, actual, None


def command(vivado: Path, result: Path, reports: Path,
            temp_dir: Path) -> list[str]:
    return [
        str(vivado), "-mode", "batch", "-nojournal", "-nolog", "-notrace",
        "-tempDir", str(temp_dir),
        "-source", str(TCL), "-tclargs", str(PROBE),
        "timing_gate_v4_stability_probe", "clk", "10.0", str(result),
        str(reports), "xc7z020clg400-1",
    ]


def infrastructure_tcl_error(stdout: str, stderr: str) -> bool:
    text = stdout + "\n" + stderr
    install_error = (
        "couldn't read file \"C:/Xilinx/Vivado/2023.1/scripts/rt/" in text
        or "cannot open file \"C:/Xilinx/Vivado/2023.1/scripts/rt/" in text
    )
    generated_error = (
        "couldn't read file " in text and ".Xil" in text
        and "realtime" in text and ".tcl" in text
        and "no such file or directory" in text
    )
    return install_error or generated_error


def run_one(index: int, vivado: Path, baseline: dict, campaign: Path,
            scratch_root: Path) -> dict:
    trial = campaign / f"run_{index:02d}"
    scratch = scratch_root / f"r{index:02d}"
    work_dir = scratch / "w"
    temp_dir = scratch / "t"
    trial.mkdir(parents=True)
    work_dir.mkdir(parents=True)
    temp_dir.mkdir(parents=True)
    before_ok, before, before_reason = dependency_guard(baseline)
    result = trial / "vivado_result.json"
    reports = trial / "reports"
    stdout_path = trial / "vivado.stdout.log"
    stderr_path = trial / "vivado.stderr.log"
    completed = None
    if before_ok:
        cmd = command(vivado, result, reports, temp_dir)
        with stdout_path.open("w", encoding="utf-8", errors="replace") as stdout, \
                stderr_path.open("w", encoding="utf-8", errors="replace") as stderr:
            completed = subprocess.run(
                subprocess.list2cmdline(cmd), cwd=work_dir, stdout=stdout,
                stderr=stderr, shell=True, check=False)
    else:
        cmd = None
        stdout_path.write_text("launch blocked by dependency guard\n", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
    after_ok, after, after_reason = dependency_guard(baseline)
    parsed = {}
    parse_error = None
    try:
        parsed = read_json(result)
    except Exception as exc:
        parse_error = str(exc)
    stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    valid = (before_ok and after_ok and completed is not None
             and completed.returncode == 0 and measurement_valid(parsed))
    if not before_ok:
        classification = before_reason
    elif not after_ok:
        classification = after_reason
    elif valid:
        classification = "VALID_SYNTHETIC_MEASUREMENT"
    elif infrastructure_tcl_error(stdout, stderr):
        classification = "vivado_internal_tcl_read_failure"
    else:
        classification = "synthetic_vivado_failure"
    return {
        "run": index,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "contains_study2_rtl": False,
        "command": cmd,
        "before_dependency_guard": {"ok": before_ok, "snapshot": before},
        "after_dependency_guard": {"ok": after_ok, "snapshot": after},
        "returncode": None if completed is None else completed.returncode,
        "parse_error": parse_error,
        "vivado": parsed,
        "valid_measurement": valid,
        "classification": classification,
        "trial_dir": trial.relative_to(ROOT).as_posix(),
        "scratch_work_dir": str(work_dir),
        "scratch_temp_dir": str(temp_dir),
        "explicit_tempdir": True,
        "stdout_sha256_raw": sha256_file(stdout_path),
        "stderr_sha256_raw": sha256_file(stderr_path),
        "result_sha256_raw": sha256_file(result) if result.is_file() else None,
    }


def build_attestation(baseline: dict, rows: list[dict], scratch_root: Path) -> dict:
    all_ok = len(rows) == RUNS and all(row["valid_measurement"] for row in rows)
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v4",
        "scope": "pre-candidate synthetic infrastructure stability gate",
        "contains_study2_rtl": False,
        "scratch_root": str(scratch_root),
        "explicit_tempdir": True,
        "baseline_sha256_raw": sha256_file(BASELINE),
        "baseline_dependency_aggregate_sha256_raw": baseline["aggregate_sha256_raw"],
        "closure_tcl_path": TCL.relative_to(ROOT).as_posix(),
        "closure_tcl_sha256_raw": sha256_file(TCL),
        "probe_path": PROBE.relative_to(ROOT).as_posix(),
        "probe_sha256_raw": sha256_file(PROBE),
        "required_first_attempts": RUNS,
        "retry_within_campaign": 0,
        "runs": rows,
        "verdict": "PASS" if all_ok else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivado", default=str(VIVADO_ROOT / "bin" / "vivado.bat"))
    parser.add_argument("--baseline", default=str(BASELINE))
    parser.add_argument("--campaign", default=str(DEFAULT_CAMPAIGN))
    parser.add_argument("--scratch-root", default=str(DEFAULT_SCRATCH_ROOT))
    args = parser.parse_args()
    campaign = Path(args.campaign)
    scratch_root = Path(args.scratch_root)
    attestation_path = campaign / "stability_attestation.json"
    try:
        if campaign.exists():
            raise RuntimeError(f"campaign directory must be new: {campaign}")
        if scratch_root.exists():
            raise RuntimeError(f"scratch root must be new: {scratch_root}")
        baseline = read_json(Path(args.baseline))
        current = raw_dependency_snapshot(VIVADO_ROOT)
        expected = dict(current)
        expected.update({
            "study_id": "timing_closure_gate_v4",
            "scope": "Vivado 2023.1 full scripts/rt raw dependency baseline before single-thread synthetic stability gate",
            "pinned_tcl_count": sum(item["path"].endswith(".tcl") for item in current["files"]),
            "raw_read_repetitions": 20,
        })
        if baseline != expected:
            raise RuntimeError("dependency baseline is absent or no longer current")
        campaign.mkdir(parents=True)
        rows = []
        for index in range(1, RUNS + 1):
            row = run_one(index, Path(args.vivado), baseline, campaign, scratch_root)
            rows.append(row)
            if not row["valid_measurement"]:
                break
        attestation = build_attestation(baseline, rows, scratch_root)
        write_json_new(attestation_path, attestation)
        print(f"STABILITY {attestation['verdict']}")
        print("attestation_sha256_raw=" + sha256_file(attestation_path))
        return 0 if attestation["verdict"] == "PASS" else 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
