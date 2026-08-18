#!/usr/bin/env python3
"""Materialize every distinct RF-arm training candidate for the pre-open gate.

The RF group logs are the authoritative record of what the two policies
actually generated.  This script writes one ``.sv`` file for every distinct,
extractable RTL candidate and a manifest that preserves its design, occurrence
count, source logs, and content hashes.  ``canonicalize.py --check-traces`` can
then audit exactly this directory before any sealed evaluation is opened.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict
from typing import Optional, Sequence


class MaterializeError(RuntimeError):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode()).hexdigest()


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        raw = handle.read()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def safe_design(design: str) -> str:
    if not isinstance(design, str) or not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*", design):
        raise MaterializeError(f"invalid design name in group log: {design!r}")
    return design


def prepare_output(directory: str) -> None:
    if os.path.exists(directory):
        entries = os.listdir(directory) if os.path.isdir(directory) else [directory]
        if entries:
            raise MaterializeError(
                f"output {directory} is not empty; refusing to mix candidate audits")
    else:
        os.makedirs(directory)


def run(paths: Sequence[str], out_dir: str, manifest_path: str) -> dict:
    if len(paths) != 2 or len(set(map(os.path.abspath, paths))) != 2:
        raise MaterializeError("exactly two distinct RF group logs are required")
    prepare_output(out_dir)
    candidates: OrderedDict[str, dict] = OrderedDict()
    source_logs = []
    group_sizes = {}
    for path in paths:
        if not os.path.isfile(path):
            raise MaterializeError(f"missing RF group log: {path}")
        groups = {}
        with open(path, encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError as exc:
                    raise MaterializeError(f"malformed JSON at {path}:{lineno}") from exc
                if not isinstance(row, dict) or not isinstance(row.get("group_index"), int):
                    raise MaterializeError(f"invalid group row at {path}:{lineno}")
                groups[row["group_index"]] = groups.get(row["group_index"], 0) + 1
                rtl = row.get("rtl")
                if not isinstance(rtl, str) or not rtl.strip():
                    continue
                design = safe_design(row.get("design"))
                normalized = rtl.replace("\r\n", "\n")
                digest = sha256_text(normalized)
                key = digest
                if key in candidates and candidates[key]["design"] != design:
                    raise MaterializeError(
                        f"byte-identical RTL appears under different designs: "
                        f"{candidates[key]['design']} and {design}")
                if key not in candidates:
                    candidates[key] = {
                        "design": design, "rtl": normalized,
                        "occurrences": 0, "source_rows": []}
                candidates[key]["occurrences"] += 1
                candidates[key]["source_rows"].append({
                    "log": os.path.abspath(path), "line": lineno,
                    "group_index": row["group_index"], "candidate": row.get("cand")})
        if not groups:
            raise MaterializeError(f"empty RF group log: {path}")
        bad = sorted(group for group, count in groups.items() if count != 8)
        if bad:
            raise MaterializeError(
                f"{path} has groups that do not contain exactly eight rows: {bad[:8]}")
        group_sizes[os.path.abspath(path)] = len(groups)
        source_logs.append({"path": os.path.abspath(path),
                            "sha256": sha256_file(path), "groups": len(groups)})

    if not candidates:
        raise MaterializeError("RF group logs contain no extractable RTL candidates")
    records = []
    for digest, row in candidates.items():
        filename = f"rftrain__{row['design']}__{digest[:16]}.sv"
        output_path = os.path.join(out_dir, filename)
        with open(output_path, "w", encoding="ascii", errors="replace",
                  newline="\n") as handle:
            handle.write(row["rtl"])
            if not row["rtl"].endswith("\n"):
                handle.write("\n")
        records.append({
            "file": os.path.relpath(output_path, os.path.dirname(manifest_path)
                                    or ".").replace(os.sep, "/"),
            "design": row["design"], "source_sha256": digest,
            "emitted_sha256": sha256_file(output_path),
            "occurrences": row["occurrences"],
            "source_rows": row["source_rows"],
        })
    manifest = {
        "schema": "rf_training_candidates/1",
        "source_logs": source_logs,
        "n_distinct_candidates": len(records),
        "n_occurrences": sum(row["occurrences"] for row in records),
        "candidates": records,
    }
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=1)
        handle.write("\n")
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group-log", action="append", required=True,
                    help="repeat exactly twice, once per RF training seed")
    ap.add_argument("--out-dir", default="rtl/sealed_rf_training_candidates")
    ap.add_argument("--manifest", default="rf_training_candidates.json")
    args = ap.parse_args(argv)
    try:
        result = run(args.group_log, args.out_dir, args.manifest)
    except MaterializeError as exc:
        print(f"candidate materialization error: {exc}", file=sys.stderr)
        return 2
    print(f"materialized {result['n_distinct_candidates']} distinct candidates "
          f"from {result['n_occurrences']} logged occurrences")
    print(f"manifest -> {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
