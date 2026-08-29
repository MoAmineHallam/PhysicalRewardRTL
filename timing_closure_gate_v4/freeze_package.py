#!/usr/bin/env python3
"""Freeze/check the prospective V4 single-thread stability package."""

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
    "launch_timing_stability_v4.ps1",
    "timing_closure_gate_v4/README.md",
    "timing_closure_gate_v4/preregistration.json",
    "timing_closure_gate_v4/closure_synth_single_thread.tcl",
    "timing_closure_gate_v4/dependency_baseline.json",
    "timing_closure_gate_v4/freeze_dependency_baseline.py",
    "timing_closure_gate_v4/freeze_package.py",
    "timing_closure_gate_v4/run_stability_gate.py",
    "timing_closure_gate_v4/stability_common.py",
    "timing_closure_gate_v4/stability_probe.sv",
    "timing_closure_gate_v4/test_stability.py",
    "timing_closure_gate_v1/manifest.json",
    "timing_closure_gate_v1/manifest.sha256",
    "timing_closure_gate_v1/closure_synth.tcl",
    "timing_closure_candidate_v3/manifest.json",
    "timing_closure_candidate_v3/manifest.sha256",
    "timing_closure_candidate_v3/results/pilot_gate.json",
    "timing_closure_candidate_v3/results/c02_fir_rf_fir42_v6_8b/closure_result.json",
    "timing_closure_candidate_v3/results/c02_fir_rf_fir42_v6_8b/trial_006_search_p5p3998125_a0/vivado.stdout.log",
    "timing_closure_candidate_v3/results/c02_fir_rf_fir42_v6_8b/trial_007_search_p5p3998125_a1/vivado.stdout.log"
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
            raise RuntimeError(f"missing V4 dependency: {relative}")
        rows.append({"path": relative, "bytes": path.stat().st_size,
                     "sha256_raw": sha256(path)})
    v3_gate = json.loads((ROOT / "timing_closure_candidate_v3/results/pilot_gate.json").read_text(encoding="utf-8"))
    if v3_gate.get("verdict") != "FAIL":
        raise RuntimeError("V3 failed gate was changed or removed")
    return {"schema_version": 1, "study_id": "timing_closure_gate_v4",
            "hash_domain": "raw bytes", "status": "frozen before first V4 process",
            "files": sorted(rows, key=lambda row: row["path"])}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = canonical(build())
    if args.write:
        if MANIFEST.exists() or MANIFEST_SHA.exists() or (HERE / "stability_campaign_001").exists():
            raise RuntimeError("refusing to overwrite or freeze after V4 outcome")
        MANIFEST.write_bytes(value)
        MANIFEST_SHA.write_text(f"{sha256(MANIFEST)}  manifest.json\n", encoding="ascii")
    else:
        if MANIFEST.read_bytes() != value:
            raise RuntimeError("V4 package manifest content mismatch")
        if MANIFEST_SHA.read_text(encoding="ascii").strip().split() != [sha256(MANIFEST), "manifest.json"]:
            raise RuntimeError("V4 package checksum mismatch")
    print("PASS v4_manifest_sha256=" + sha256(MANIFEST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
