#!/usr/bin/env python3
"""Freeze/check the prospective V6 persistent-parent package."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = HERE / "manifest.json"
MANIFEST_SHA = HERE / "manifest.sha256"
PACKAGE_INPUTS = (
    ".gitattributes",
    "launch_timing_stability_v6.ps1",
    "timing_closure_gate_v6/README.md",
    "timing_closure_gate_v6/preregistration.json",
    "timing_closure_gate_v6/persistent_closure.tcl",
    "timing_closure_gate_v6/dependency_baseline.json",
    "timing_closure_gate_v6/freeze_dependency_baseline.py",
    "timing_closure_gate_v6/freeze_package.py",
    "timing_closure_gate_v6/run_stability_gate.py",
    "timing_closure_gate_v6/test_stability.py",
    "timing_closure_gate_v4/stability_common.py",
    "timing_closure_gate_v4/stability_probe.sv",
    "timing_closure_gate_v1/closure_synth.tcl",
    "timing_closure_gate_v5/stability_campaign_001/stability_attestation.json",
    "timing_closure_gate_v5/stability_campaign_001/stability_attestation.sha256",
    "vivado_diagnostics/persistent_two_run_probe.tcl",
    "vivado_diagnostics/evidence/persistent_two_run_20260830/result.txt",
    "vivado_diagnostics/evidence/persistent_two_run_20260830/stdout.log",
    "vivado_diagnostics/evidence/persistent_two_run_20260830/stderr.log",
    "vivado_diagnostics/persistent_project_two_run_probe.tcl",
    "vivado_diagnostics/evidence/persistent_project_two_run_20260830/result.txt",
    "vivado_diagnostics/evidence/persistent_project_two_run_20260830/stdout.log",
    "vivado_diagnostics/evidence/persistent_project_two_run_20260830/stderr.log",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def build() -> dict:
    rows = []
    for relative in PACKAGE_INPUTS:
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"missing V6 dependency: {relative}")
        rows.append({"path": relative, "bytes": path.stat().st_size,
                     "sha256_raw": sha256(path)})
    v5 = json.loads((ROOT / "timing_closure_gate_v5" /
                     "stability_campaign_001" /
                     "stability_attestation.json").read_text(encoding="utf-8"))
    if v5.get("verdict") != "FAIL":
        raise RuntimeError("V5 failed gate was changed or removed")
    diagnostic = (ROOT / "vivado_diagnostics" / "evidence" /
                  "persistent_project_two_run_20260830" / "result.txt")
    diagnostic_lines = diagnostic.read_text(encoding="utf-8").splitlines()
    if len(diagnostic_lines) != 2 or not all("ok=1" in line for line in diagnostic_lines):
        raise RuntimeError("persistent in-memory-project diagnostic changed")
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v6",
        "hash_domain": "raw bytes",
        "status": "frozen before first V6 stability process",
        "files": sorted(rows, key=lambda row: row["path"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = canonical(build())
    if args.write:
        if (MANIFEST.exists() or MANIFEST_SHA.exists() or
                (HERE / "stability_campaign_001").exists()):
            raise RuntimeError("refusing to overwrite or freeze after V6 outcome")
        MANIFEST.write_bytes(value)
        MANIFEST_SHA.write_text(
            f"{sha256(MANIFEST)}  manifest.json\n", encoding="ascii")
    else:
        if MANIFEST.read_bytes() != value:
            raise RuntimeError("V6 package manifest content mismatch")
        if MANIFEST_SHA.read_text(encoding="ascii").strip().split() != [
                sha256(MANIFEST), "manifest.json"]:
            raise RuntimeError("V6 package checksum mismatch")
    print("PASS v6_manifest_sha256=" + sha256(MANIFEST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
