#!/usr/bin/env python3
"""Run/check a synthetic Vivado capability probe before manifest freeze."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = HERE / "preflight_probe.sv"
TCL = HERE / "closure_synth.tcl"
OUT = HERE / "preflight"
RESULT = OUT / "vivado_result.json"
STDOUT = OUT / "vivado.stdout.log"
STDERR = OUT / "vivado.stderr.log"
REPORTS = OUT / "reports"
ATTESTATION = OUT / "capability_preflight.json"


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    os.replace(temp, path)


def assert_no_candidate_results():
    results = HERE / "results"
    if results.exists() and any(results.rglob("closure_result.json")):
        raise RuntimeError(
            "candidate result exists; capability preflight is no longer pre-outcome")
    if results.exists() and any(results.rglob("trials.jsonl")):
        raise RuntimeError(
            "candidate trial ledger exists; capability preflight is no longer pre-outcome")


def command(vivado):
    return [
        str(vivado), "-mode", "batch", "-nojournal", "-nolog", "-notrace",
        "-source", str(TCL), "-tclargs", str(SOURCE),
        "timing_gate_preflight_probe", "clk", "10.0", str(RESULT),
        str(REPORTS), "xc7z020clg400-1",
    ]


def inspect():
    required_files = [RESULT, STDOUT, STDERR, REPORTS / "constraints.xdc",
                      REPORTS / "clocks_post_synth.rpt",
                      REPORTS / "route_status.rpt",
                      REPORTS / "timing_summary.rpt"]
    missing = [rel(path) for path in required_files if not path.is_file()]
    if missing:
        raise RuntimeError(f"preflight outputs missing: {missing}")
    record = json.loads(RESULT.read_text(encoding="utf-8"))
    stdout = STDOUT.read_text(encoding="utf-8", errors="replace")
    tcl_lines = [line.strip() for line in TCL.read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
    read_index = next(index for index, line in enumerate(tcl_lines)
                      if line.startswith("read_xdc "))
    synth_index = next(index for index, line in enumerate(tcl_lines)
                       if line.startswith("synth_design "))
    checks = {
        "vivado_2023_1": bool(re.search(r"Vivado\s+v2023\.1", stdout)),
        "read_xdc_before_synth": read_index < synth_index,
        "synthesis_and_implementation": (
            int(record.get("compiled", 0)) == 1
            and int(record.get("implemented", 0)) == 1
            and int(record.get("stage_code", -1)) == 0
        ),
        "one_clock": int(record.get("clock_count", 0)) == 1,
        "setup_path_exists": int(record.get("setup_path_count", 0)) > 0,
        "design_timing_summary_parsed": int(record.get("summary_parse_ok", 0)) == 1,
        "check_timing_unconstrained_zero": (
            int(record.get("unconstrained_path_count", -1)) == 0
        ),
        "input_delays_covered": (
            int(record.get("no_input_delay_count", -1)) == 0
            and int(record.get("partial_input_delay_count", -1)) == 0
            and int(record.get("input_delay_count", -1))
                == int(record.get("nonclock_input_count", -2))
        ),
        "output_delays_covered": (
            int(record.get("no_output_delay_count", -1)) == 0
            and int(record.get("partial_output_delay_count", -1)) == 0
            and int(record.get("output_delay_count", -1))
                == int(record.get("output_count", -2))
        ),
        "constraint_coverage": int(record.get("constraint_coverage_ok", 0)) == 1,
        "route_status_filter_supported_and_clean": (
            int(record.get("unrouted_net_count", -1)) == 0
            and int(record.get("route_clean", 0)) == 1
        ),
    }
    files = []
    for path in sorted((path for path in OUT.rglob("*") if path.is_file()
                        and path != ATTESTATION), key=lambda item: item.as_posix()):
        files.append({"path": rel(path), "sha256": sha256_file(path)})
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v1",
        "scope": "synthetic_capability_preflight",
        "uses_study2_candidate": False,
        "source_path": rel(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "closure_tcl_sha256": sha256_file(TCL),
        "vivado_result": record,
        "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "files": files,
    }


def run(vivado):
    assert_no_candidate_results()
    if OUT.exists() and any(OUT.iterdir()):
        raise RuntimeError(
            "preflight directory is nonempty; use --check or preserve it and "
            "create a disclosed revision")
    OUT.mkdir(parents=True, exist_ok=True)
    with STDOUT.open("w", encoding="utf-8", errors="replace") as stdout, \
            STDERR.open("w", encoding="utf-8", errors="replace") as stderr:
        cmd = command(vivado)
        if os.name == "nt":
            completed = subprocess.run(
                subprocess.list2cmdline(cmd), cwd=OUT, stdout=stdout,
                stderr=stderr, shell=True, check=False)
        else:
            completed = subprocess.run(
                cmd, cwd=OUT, stdout=stdout, stderr=stderr, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Vivado preflight exited {completed.returncode}")
    attestation = inspect()
    atomic_json(ATTESTATION, attestation)
    return attestation


def check():
    if not ATTESTATION.is_file():
        raise RuntimeError("capability_preflight.json is missing")
    frozen = json.loads(ATTESTATION.read_text(encoding="utf-8"))
    actual = inspect()
    if frozen != actual:
        raise RuntimeError("preflight attestation or a pinned output changed")
    return actual


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--vivado", default="vivado")
    args = parser.parse_args()
    try:
        attestation = run(args.vivado) if args.run else check()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"PREFLIGHT {attestation['verdict']}")
    for key, value in attestation["checks"].items():
        print(f"  {key}: {value}")
    print(f"attestation_sha256={sha256_file(ATTESTATION)}")
    return 0 if attestation["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
