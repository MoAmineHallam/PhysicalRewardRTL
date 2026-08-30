#!/usr/bin/env python3
"""Freeze/check the prospective V5 post-restart stability package."""

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
    "launch_timing_stability_v5.ps1",
    "timing_closure_gate_v5/README.md",
    "timing_closure_gate_v5/preregistration.json",
    "timing_closure_gate_v5/dependency_baseline.json",
    "timing_closure_gate_v5/freeze_dependency_baseline.py",
    "timing_closure_gate_v5/freeze_package.py",
    "timing_closure_gate_v5/run_stability_gate.py",
    "timing_closure_gate_v5/test_stability.py",
    "timing_closure_gate_v4/manifest.json",
    "timing_closure_gate_v4/manifest.sha256",
    "timing_closure_gate_v4/closure_synth_single_thread.tcl",
    "timing_closure_gate_v4/run_stability_gate.py",
    "timing_closure_gate_v4/stability_common.py",
    "timing_closure_gate_v4/stability_probe.sv",
    "timing_closure_gate_v4/stability_campaign_001/stability_attestation.json",
    "timing_closure_gate_v4/stability_campaign_001/stability_attestation.sha256",
    "vivado_diagnostics/minimal_synth_probe.tcl",
    "vivado_diagnostics/minimal_probe.sv",
    "vivado_diagnostics/evidence/postrestart_20260830__r01/result.txt",
    "vivado_diagnostics/evidence/postrestart_20260830__r01/stdout.log",
    "vivado_diagnostics/evidence/postrestart_20260830__r01/stderr.log",
    "vivado_diagnostics/evidence/postrestart_20260830__r01/run_metadata.txt",
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
            raise RuntimeError(f"missing V5 dependency: {relative}")
        rows.append({"path": relative, "bytes": path.stat().st_size,
                     "sha256_raw": sha256(path)})
    v4 = json.loads((ROOT / "timing_closure_gate_v4" /
                     "stability_campaign_001" /
                     "stability_attestation.json").read_text(encoding="utf-8"))
    if v4.get("verdict") != "FAIL":
        raise RuntimeError("V4 failed gate was changed or removed")
    post_restart = (ROOT / "vivado_diagnostics" / "evidence" /
                    "postrestart_20260830__r01" / "result.txt")
    if post_restart.read_text(encoding="ascii").splitlines()[0] != "SYNTH_PASS":
        raise RuntimeError("post-restart diagnostic evidence changed")
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v5",
        "hash_domain": "raw bytes",
        "status": "frozen before first V5 process",
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
            raise RuntimeError("refusing to overwrite or freeze after V5 outcome")
        MANIFEST.write_bytes(value)
        MANIFEST_SHA.write_text(
            f"{sha256(MANIFEST)}  manifest.json\n", encoding="ascii")
    else:
        if MANIFEST.read_bytes() != value:
            raise RuntimeError("V5 package manifest content mismatch")
        if MANIFEST_SHA.read_text(encoding="ascii").strip().split() != [
                sha256(MANIFEST), "manifest.json"]:
            raise RuntimeError("V5 package checksum mismatch")
    print("PASS v5_manifest_sha256=" + sha256(MANIFEST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
