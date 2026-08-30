#!/usr/bin/env python3
"""Freeze/check the raw-byte Vivado dependency baseline for V6."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from timing_closure_gate_v4.stability_common import (
    VIVADO_ROOT, raw_dependency_snapshot, read_json, sha256_file,
    write_json_new,
)

HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "dependency_baseline.json"
BASELINE_READ_REPETITIONS = 20


def build() -> dict:
    snapshot = raw_dependency_snapshot(VIVADO_ROOT)
    for _ in range(1, BASELINE_READ_REPETITIONS):
        if raw_dependency_snapshot(VIVADO_ROOT) != snapshot:
            raise RuntimeError("Vivado dependency bytes changed during baseline reads")
    snapshot.update({
        "study_id": "timing_closure_gate_v6",
        "scope": "Vivado 2023.1 full scripts/rt baseline before persistent-parent stability gate",
        "pinned_tcl_count": sum(
            item["path"].endswith(".tcl") for item in snapshot["files"]),
        "raw_read_repetitions": BASELINE_READ_REPETITIONS,
    })
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    output = Path(args.output)
    try:
        actual = build()
        if args.write:
            write_json_new(output, actual)
            frozen = actual
        else:
            frozen = read_json(output)
            if frozen != actual:
                raise RuntimeError("Vivado raw dependency baseline changed")
        print("PASS dependency_baseline_sha256=" + sha256_file(output))
        print("PASS dependency_aggregate_sha256_raw=" +
              frozen["aggregate_sha256_raw"])
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
