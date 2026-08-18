#!/usr/bin/env python3
"""Verify complete one-row-per-candidate Vivado outputs for the sealed study."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from typing import Optional, Sequence


DEFAULT_DIRS = [
    "rtl/sealed_sft",
    "rtl/sealed_rf_s1", "rtl/sealed_rf_s2",
    "rtl/sealed_rf_mid_s1", "rtl/sealed_rf_mid_s2",
    "rtl/sealed_mlp_s1", "rtl/sealed_mlp_s2",
    "rtl/sealed_corr_s1",
]


class PPAError(RuntimeError):
    pass


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        raw = handle.read()
    if os.path.splitext(path)[1].lower() in {
            ".py", ".tcl", ".json", ".jsonl", ".sv", ".v", ".sh", ".ps1"}:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def read_json(path: str):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        raise PPAError(f"cannot read {path}: {exc}") from exc


def verify_directory(directory: str) -> dict:
    manifest_path = os.path.join(directory, "fmax_manifest.json")
    ppa_path = os.path.join(directory, "ppa.jsonl")
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict) or not manifest:
        raise PPAError(f"{manifest_path} is empty or not an object")
    modules = set(manifest)
    rows = {}
    try:
        handle = open(ppa_path, encoding="utf-8")
    except OSError as exc:
        raise PPAError(f"cannot read {ppa_path}: {exc}") from exc
    with handle:
        for lineno, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise PPAError(f"malformed JSON at {ppa_path}:{lineno}") from exc
            module = row.get("module") if isinstance(row, dict) else None
            if module not in modules:
                raise PPAError(f"unknown module at {ppa_path}:{lineno}: {module!r}")
            if module in rows:
                raise PPAError(f"duplicate PPA row for {module} in {ppa_path}")
            if row.get("compiled") not in (0, 1, False, True):
                raise PPAError(f"invalid compiled status for {module}")
            if row.get("compiled"):
                for key in ("fmax_mhz", "lut", "ff", "dsp", "bram", "power_w"):
                    try:
                        value = float(row[key])
                    except (KeyError, TypeError, ValueError) as exc:
                        raise PPAError(f"compiled row {module} lacks numeric {key}") from exc
                    if not math.isfinite(value) or value < 0:
                        raise PPAError(f"compiled row {module} has invalid {key}={value}")
            rows[module] = row
    missing = modules - set(rows)
    if missing:
        raise PPAError(
            f"{directory} is incomplete: {len(missing)} candidates lack PPA rows")
    return {
        "directory": os.path.abspath(directory),
        "manifest_sha256": sha256_file(manifest_path),
        "ppa_sha256": sha256_file(ppa_path),
        "n_candidates": len(modules),
        "n_compiled": sum(bool(row.get("compiled")) for row in rows.values()),
        "n_failed": sum(not bool(row.get("compiled")) for row in rows.values()),
    }


def run(directories: Sequence[str], output: str, vivado: str, period: float) -> dict:
    if len(directories) != len(set(map(os.path.abspath, directories))):
        raise PPAError("duplicate evaluation directories")
    tcl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ppa_synth.tcl")
    with open(tcl_path, encoding="utf-8") as handle:
        tcl = handle.read()
    match = re.search(r"^set\s+part\s+(\S+)", tcl, re.MULTILINE)
    if not match:
        raise PPAError("cannot determine target part from ppa_synth.tcl")
    result = {
        "schema": "sealed_ppa_audit/1",
        "complete": True,
        "vivado": vivado,
        "period_ns": period,
        "target_part": match.group(1),
        "run_ppa_sha256": sha256_file("run_ppa.py"),
        "ppa_tcl_sha256": sha256_file(tcl_path),
        "directories": [verify_directory(directory) for directory in directories],
    }
    with open(output, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=1)
        handle.write("\n")
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", action="append", dest="directories")
    ap.add_argument("--vivado", default=r"C:\Xilinx\Vivado\2023.1\bin\vivado.bat")
    ap.add_argument("--period", type=float, default=5.0)
    ap.add_argument("--out", default="sealed_ppa_audit.json")
    args = ap.parse_args(argv)
    try:
        result = run(args.directories or DEFAULT_DIRS, args.out,
                     args.vivado, args.period)
    except PPAError as exc:
        print(f"sealed PPA audit error: {exc}", file=sys.stderr)
        return 2
    total = sum(row["n_candidates"] for row in result["directories"])
    failed = sum(row["n_failed"] for row in result["directories"])
    print(f"PASS: {total} candidate PPA rows complete; {failed} explicit failures")
    print(f"audit -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
