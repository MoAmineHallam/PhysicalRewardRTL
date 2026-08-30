#!/usr/bin/env python3
"""Freeze/check the prospective Vivado-2026.1 stability package V7."""

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
    "launch_timing_stability_v7.ps1",
    "timing_closure_gate_v7/__init__.py",
    "timing_closure_gate_v7/README.md",
    "timing_closure_gate_v7/preregistration.json",
    "timing_closure_gate_v7/preflight.tcl",
    "timing_closure_gate_v7/dependency_baseline.json",
    "timing_closure_gate_v7/stability_common.py",
    "timing_closure_gate_v7/freeze_dependency_baseline.py",
    "timing_closure_gate_v7/freeze_package.py",
    "timing_closure_gate_v7/run_stability_gate.py",
    "timing_closure_gate_v7/test_stability.py",
    "timing_closure_gate_v1/closure_synth.tcl",
    "timing_closure_gate_v4/stability_common.py",
    "timing_closure_gate_v4/stability_probe.sv",
    "timing_closure_gate_v5/manifest.json",
    "timing_closure_gate_v5/manifest.sha256",
    "timing_closure_gate_v5/stability_campaign_001/stability_attestation.json",
    "timing_closure_gate_v5/stability_campaign_001/stability_attestation.sha256",
    "timing_closure_gate_v6/manifest.json",
    "timing_closure_gate_v6/manifest.sha256",
    "timing_closure_gate_v6/stability_campaign_001/stability_attestation.json",
    "timing_closure_gate_v6/stability_campaign_001/stability_attestation.sha256",
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
            raise RuntimeError(f"missing V7 dependency: {relative}")
        rows.append({"path": relative, "bytes": path.stat().st_size,
                     "sha256_raw": sha256(path)})
    for version in ("v5", "v6"):
        attestation = json.loads((
            ROOT / f"timing_closure_gate_{version}" /
            "stability_campaign_001" / "stability_attestation.json"
        ).read_text(encoding="utf-8"))
        if attestation.get("verdict") != "FAIL":
            raise RuntimeError(f"{version.upper()} failed gate changed or removed")
    baseline = json.loads((HERE / "dependency_baseline.json").read_text(
        encoding="utf-8"))
    if baseline.get("vivado_version") != "2026.1":
        raise RuntimeError("V7 baseline is not bound to Vivado 2026.1")
    if Path(baseline.get("vivado_root", "")) != Path(
            r"C:\AMD\2026.1\Vivado"):
        raise RuntimeError("V7 baseline is not bound to the side-by-side install")
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v7",
        "hash_domain": "raw bytes",
        "status": "frozen before first Vivado-2026.1 synthesis",
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
            raise RuntimeError(
                "refusing to overwrite or freeze after a V7 outcome")
        MANIFEST.write_bytes(value)
        MANIFEST_SHA.write_text(
            f"{sha256(MANIFEST)}  manifest.json\n", encoding="ascii")
    else:
        if MANIFEST.read_bytes() != value:
            raise RuntimeError("V7 package manifest content mismatch")
        if MANIFEST_SHA.read_text(encoding="ascii").strip().split() != [
                sha256(MANIFEST), "manifest.json"]:
            raise RuntimeError("V7 package checksum mismatch")
    print("PASS v7_manifest_sha256=" + sha256(MANIFEST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
