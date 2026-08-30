#!/usr/bin/env python3
"""Run the V6 persistent-parent in-memory-project stability gate."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from timing_closure_gate_v4.stability_common import (
    ROOT, VIVADO_ROOT, measurement_valid, raw_dependency_snapshot, read_json,
    sha256_file, write_json_new,
)

HERE = Path(__file__).resolve().parent
TCL = HERE / "persistent_closure.tcl"
PROBE = ROOT / "timing_closure_gate_v4" / "stability_probe.sv"
BASELINE = HERE / "dependency_baseline.json"
DEFAULT_CAMPAIGN = HERE / "stability_campaign_001"
DEFAULT_SCRATCH_ROOT = Path(r"C:\VGT6P001")
RUNS = 40
GUARD_READ_PASSES = 3
MAX_WNS_SPREAD_NS = 0.001
REQUIRED_HELPER_LAUNCHES = 1


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


def command(vivado: Path, campaign: Path, temp_dir: Path) -> list[str]:
    return [
        str(vivado), "-mode", "batch", "-nojournal", "-nolog", "-notrace",
        "-tempDir", str(temp_dir), "-source", str(TCL), "-tclargs",
        str(PROBE), "timing_gate_v4_stability_probe", "clk", "10.0",
        str(campaign), str(RUNS), "xc7z020clg400-1",
    ]


def row_for(index: int, campaign: Path) -> dict:
    trial = campaign / f"run_{index:02d}"
    result = trial / "vivado_result.json"
    parsed = {}
    parse_error = None
    try:
        parsed = read_json(result)
    except Exception as exc:
        parse_error = str(exc)
    isolation = (
        int(parsed.get("projects_before", -1)) == 0
        and int(parsed.get("projects_after", -1)) == 0
        and int(parsed.get("files_before", -1)) == 0
        and int(parsed.get("files_after", -1)) == 0
        and int(parsed.get("session_isolation_ok", 0)) == 1
    )
    valid = parse_error is None and measurement_valid(parsed) and isolation
    return {
        "run": index,
        "trial_dir": trial.relative_to(ROOT).as_posix(),
        "parse_error": parse_error,
        "vivado": parsed,
        "session_isolation_valid": isolation,
        "valid_measurement": valid,
        "result_sha256_raw": sha256_file(result) if result.is_file() else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivado", default=str(
        VIVADO_ROOT / "bin" / "vivado.bat"))
    parser.add_argument("--baseline", default=str(BASELINE))
    parser.add_argument("--campaign", default=str(DEFAULT_CAMPAIGN))
    parser.add_argument("--scratch-root", default=str(DEFAULT_SCRATCH_ROOT))
    args = parser.parse_args()
    campaign = Path(args.campaign)
    scratch_root = Path(args.scratch_root)
    try:
        if campaign.exists():
            raise RuntimeError(f"campaign directory must be new: {campaign}")
        if scratch_root.exists():
            raise RuntimeError(f"scratch root must be new: {scratch_root}")
        baseline = read_json(Path(args.baseline))
        current = raw_dependency_snapshot(VIVADO_ROOT)
        expected = dict(current)
        expected.update({
            "study_id": "timing_closure_gate_v6",
            "scope": "Vivado 2023.1 full scripts/rt baseline before persistent-parent stability gate",
            "pinned_tcl_count": sum(
                item["path"].endswith(".tcl") for item in current["files"]),
            "raw_read_repetitions": 20,
        })
        if baseline != expected:
            raise RuntimeError("dependency baseline is absent or no longer current")
        campaign.mkdir(parents=True)
        work_dir = scratch_root / "w"
        temp_dir = scratch_root / "t"
        work_dir.mkdir(parents=True)
        temp_dir.mkdir(parents=True)
        before_ok, before, before_reason = dependency_guard(baseline)
        stdout_path = campaign / "vivado.stdout.log"
        stderr_path = campaign / "vivado.stderr.log"
        cmd = command(Path(args.vivado), campaign, temp_dir)
        completed = None
        started = datetime.now(timezone.utc).isoformat()
        if before_ok:
            with stdout_path.open("w", encoding="utf-8", errors="replace") as stdout, \
                    stderr_path.open("w", encoding="utf-8", errors="replace") as stderr:
                completed = subprocess.run(
                    subprocess.list2cmdline(cmd), cwd=work_dir, stdout=stdout,
                    stderr=stderr, shell=True, check=False)
        else:
            stdout_path.write_text("launch blocked by dependency guard\n",
                                   encoding="utf-8")
            stderr_path.write_text("", encoding="utf-8")
        after_ok, after, after_reason = dependency_guard(baseline)
        rows = [row_for(index, campaign) for index in range(1, RUNS + 1)]
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
        helper_launches = stdout.count("Helper process launched with PID")
        stdout_internal_error = ("couldn't read file" in stdout or
                                 "cannot open file" in stdout)
        stderr_internal_error = ("couldn't read file" in stderr or
                                 "cannot open file" in stderr)
        valid_rows = [row for row in rows if row["valid_measurement"]]
        wns_values = [float(row["vivado"]["wns_ns"]) for row in valid_rows]
        wns_spread = (max(wns_values) - min(wns_values)
                      if len(wns_values) == RUNS else None)
        all_ok = (
            before_ok and after_ok and completed is not None
            and completed.returncode == 0 and len(valid_rows) == RUNS
            and helper_launches == REQUIRED_HELPER_LAUNCHES
            and wns_spread is not None and wns_spread <= MAX_WNS_SPREAD_NS
            and not stdout_internal_error and not stderr_internal_error
        )
        attestation = {
            "schema_version": 1,
            "study_id": "timing_closure_gate_v6",
            "scope": "persistent-parent pre-candidate synthetic infrastructure gate",
            "contains_study2_rtl": False,
            "started_utc": started,
            "ended_utc": datetime.now(timezone.utc).isoformat(),
            "command": cmd,
            "scratch_work_dir": str(work_dir),
            "scratch_temp_dir": str(temp_dir),
            "parent_process_count": 1,
            "required_iterations": RUNS,
            "retry_count": 0,
            "required_helper_launch_count": REQUIRED_HELPER_LAUNCHES,
            "observed_helper_launch_count": helper_launches,
            "maximum_wns_spread_ns": MAX_WNS_SPREAD_NS,
            "observed_wns_spread_ns": wns_spread,
            "before_dependency_guard": {"ok": before_ok, "reason": before_reason,
                                         "snapshot": before},
            "after_dependency_guard": {"ok": after_ok, "reason": after_reason,
                                        "snapshot": after},
            "returncode": None if completed is None else completed.returncode,
            "stdout_sha256_raw": sha256_file(stdout_path),
            "stderr_sha256_raw": sha256_file(stderr_path),
            "stdout_internal_tcl_error": stdout_internal_error,
            "stderr_internal_tcl_error": stderr_internal_error,
            "rows": rows,
            "verdict": "PASS" if all_ok else "FAIL",
        }
        attestation_path = campaign / "stability_attestation.json"
        write_json_new(attestation_path, attestation)
        print(f"STABILITY {attestation['verdict']}")
        print("attestation_sha256_raw=" + sha256_file(attestation_path))
        return 0 if all_ok else 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
