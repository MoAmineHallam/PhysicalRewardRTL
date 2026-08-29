#!/usr/bin/env python3
"""Freeze or verify the pre-outcome candidate-V3 package by raw bytes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from .common import (HERE, ROOT, PACKAGE_MANIFEST, PACKAGE_SHA,
                         canonical_json_bytes, sha256_file, verify_inputs)
except ImportError:
    from common import (HERE, ROOT, PACKAGE_MANIFEST, PACKAGE_SHA,
                        canonical_json_bytes, sha256_file, verify_inputs)


LOCAL_FILES = (
    "__init__.py", "README.md", "preregistration.json", "common.py",
    "run_candidates.py", "validate.py", "test_candidate.py",
    "freeze_package.py",
)
ROOT_FILES = ("launch_timing_candidates_v3.ps1",)


def dependency_paths() -> list[Path]:
    paths = [HERE / name for name in LOCAL_FILES]
    paths.extend(ROOT / name for name in ROOT_FILES)
    v1 = ROOT / "timing_closure_gate_v1"
    paths.extend([v1 / "manifest.json", v1 / "manifest.sha256",
                  v1 / "closure_synth.tcl"])
    paths.extend(sorted((v1 / "inputs").glob("*.sv")))
    v3 = ROOT / "timing_closure_gate_v3"
    paths.extend([v3 / "manifest.json", v3 / "manifest.sha256",
                  v3 / "dependency_baseline.json",
                  v3 / "stability_campaign_001" / "stability_attestation.json",
                  v3 / "stability_campaign_001" / "stability_attestation.sha256"])
    return paths


def build_manifest() -> dict:
    verify_inputs()
    rows = []
    for path in dependency_paths():
        if not path.is_file():
            raise RuntimeError(f"missing candidate package dependency: {path}")
        rows.append({"path": path.relative_to(ROOT).as_posix(),
                     "bytes": path.stat().st_size,
                     "sha256_raw": sha256_file(path)})
    return {"schema_version": 1,
            "study_id": "timing_closure_candidate_v3",
            "hash_domain": "raw bytes",
            "status": "frozen before first V3 candidate process",
            "files": sorted(rows, key=lambda row: row["path"])}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        value = build_manifest()
        raw = canonical_json_bytes(value)
        if args.write:
            if (HERE / "results").exists() or Path(r"C:\VGC3P001").exists():
                raise RuntimeError(
                    "candidate results/scratch already exist; pre-outcome freeze refused")
            if PACKAGE_MANIFEST.exists() or PACKAGE_SHA.exists():
                raise RuntimeError("candidate package is already frozen")
            PACKAGE_MANIFEST.write_bytes(raw)
            digest = sha256_file(PACKAGE_MANIFEST)
            PACKAGE_SHA.write_text(f"{digest}  manifest.json\n", encoding="ascii")
        else:
            if PACKAGE_MANIFEST.read_bytes() != raw:
                raise RuntimeError("candidate package manifest content mismatch")
            digest = sha256_file(PACKAGE_MANIFEST)
            fields = PACKAGE_SHA.read_text(encoding="ascii").strip().split()
            if fields != [digest, "manifest.json"]:
                raise RuntimeError("candidate package SHA line mismatch")
        print(f"PASS candidate_package_sha256={digest}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
