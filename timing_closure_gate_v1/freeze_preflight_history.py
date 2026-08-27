#!/usr/bin/env python3
"""Freeze relocated failed synthetic preflight attempts without rewriting them."""

import argparse
import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTPUT = HERE / "preflight_history.json"
ATTEMPTS = (
    "preflight_attempt1_unsupported_queries",
    "preflight_attempt2_empty_get_timing_paths",
)


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build():
    attempts = []
    for name in ATTEMPTS:
        directory = HERE / name
        attestation = directory / "capability_preflight.json"
        if not attestation.is_file():
            raise RuntimeError(f"missing preserved attestation: {attestation}")
        files = []
        for path in sorted((item for item in directory.rglob("*") if item.is_file()),
                           key=lambda item: item.as_posix()):
            files.append({
                "path": path.resolve().relative_to(ROOT).as_posix(),
                "sha256": sha256_file(path),
            })
        attempts.append({
            "directory": directory.resolve().relative_to(ROOT).as_posix(),
            "original_attestation_sha256": sha256_file(attestation),
            "files": files,
        })
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v1",
        "scope": "preserved_synthetic_preflight_failures",
        "candidate_trials_existed": False,
        "attempts": attempts,
    }


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        expected = encoded(build())
        if args.write:
            if OUTPUT.exists() and OUTPUT.read_bytes() != expected:
                raise RuntimeError("refusing to overwrite divergent preflight history")
            if not OUTPUT.exists():
                OUTPUT.write_bytes(expected)
        elif not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            raise RuntimeError("preflight history is missing or stale")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: preflight_history_sha256={sha256_file(OUTPUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

