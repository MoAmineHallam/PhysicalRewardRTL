#!/usr/bin/env python3
"""Vivado-2026.1 dependency binding and helpers for timing gate V7."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from timing_closure_gate_v4.stability_common import (  # noqa: E402
    canonical_json_bytes,
    measurement_valid,
    raw_dependency_snapshot as _raw_dependency_snapshot,
    read_json,
    sha256_bytes,
    sha256_file,
    write_json_new,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VIVADO_ROOT = Path(r"C:\AMD\2026.1\Vivado")


def raw_dependency_snapshot(vivado_root: Path = VIVADO_ROOT) -> dict:
    """Bind the V7 gate to the new installation, never the 2023.1 tree."""
    return _raw_dependency_snapshot(Path(vivado_root))


__all__ = (
    "HERE", "ROOT", "VIVADO_ROOT", "canonical_json_bytes",
    "measurement_valid", "raw_dependency_snapshot", "read_json",
    "sha256_bytes", "sha256_file", "write_json_new",
)
