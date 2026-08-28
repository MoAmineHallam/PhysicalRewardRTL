#!/usr/bin/env python3
"""Raw-byte dependency guards and small helpers for timing-gate v2."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VIVADO_ROOT = Path(r"C:\Xilinx\Vivado\2023.1")
DEPENDENCY_RELATIVE_PATHS = (
    "bin/vivado.bat",
    "bin/unwrapped/win64.o/vivado.exe",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def write_json_new(path: Path, value: Any) -> None:
    """Atomically publish a new artifact; never replace an accepted record."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise RuntimeError(f"refusing to overwrite existing artifact: {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_bytes(canonical_json_bytes(value))
        if path.exists():
            raise RuntimeError(f"artifact appeared during publication: {path}")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def raw_dependency_snapshot(vivado_root: Path = VIVADO_ROOT) -> dict[str, Any]:
    """Return raw-byte identity for every pinned Vivado executable/Tcl file."""
    vivado_root = Path(vivado_root)
    paths = [vivado_root / relative for relative in DEPENDENCY_RELATIVE_PATHS]
    tcl_root = vivado_root / "scripts" / "rt" / "data"
    if not tcl_root.is_dir():
        raise RuntimeError(f"Vivado Tcl root is missing: {tcl_root}")
    paths.extend(sorted(tcl_root.rglob("*.tcl"), key=lambda item: item.as_posix()))
    records = []
    for path in paths:
        if not path.is_file():
            raise RuntimeError(f"pinned Vivado dependency is missing: {path}")
        raw = path.read_bytes()
        records.append({
            "path": path.relative_to(vivado_root).as_posix(),
            "bytes": len(raw),
            "sha256_raw": sha256_bytes(raw),
        })
    digest = hashlib.sha256()
    for record in records:
        digest.update(record["path"].encode("utf-8") + b"\0")
        digest.update(str(record["bytes"]).encode("ascii") + b"\0")
        digest.update(record["sha256_raw"].encode("ascii") + b"\n")
    return {
        "schema_version": 1,
        "hash_domain": "raw bytes; no newline or text normalization",
        "vivado_root": str(vivado_root),
        "files": records,
        "aggregate_sha256_raw": digest.hexdigest(),
    }


def measurement_valid(record: dict[str, Any]) -> bool:
    required = (
        int(record.get("compiled", 0)) == 1,
        int(record.get("implemented", 0)) == 1,
        int(record.get("clock_count", 0)) == 1,
        int(record.get("setup_path_count", 0)) > 0,
        int(record.get("summary_parse_ok", 0)) == 1,
        int(record.get("unconstrained_path_count", -1)) == 0,
        int(record.get("route_clean", 0)) == 1,
        int(record.get("constraint_coverage_ok", 0)) == 1,
    )
    return all(required) and math.isfinite(float(record.get("wns_ns", math.nan)))


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
