#!/usr/bin/env python3
"""Deterministic serialization, hashing, and frozen-path helpers."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
V1 = ROOT / "timing_closure_gate_v1"
V1_MANIFEST_SHA256 = "2e0674f96c57be3864a6fab7683b0edc76f732762f78547d5e6a3e8efc17e194"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def write_json_atomic(path: Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_json_bytes(value))
    os.replace(temporary, path)


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_v1_manifest() -> tuple[dict[str, Any], str]:
    manifest_path = V1 / "manifest.json"
    digest = sha256_file(manifest_path)
    if digest != V1_MANIFEST_SHA256:
        raise RuntimeError(f"v1 manifest changed: {digest}")
    sha_line = (V1 / "manifest.sha256").read_text(encoding="ascii").strip().split()[0].lower()
    if sha_line != digest:
        raise RuntimeError("v1 manifest.sha256 disagrees with manifest.json")
    manifest = load_json(manifest_path)
    if manifest.get("study_id") != "timing_closure_gate_v1" or len(manifest.get("candidates", [])) != 10:
        raise RuntimeError("unexpected v1 manifest identity")
    for candidate in manifest["candidates"]:
        source = ROOT / candidate["materialized_path"]
        if sha256_file(source) != candidate["emitted_sha256"]:
            raise RuntimeError(f"v1 materialized input changed: {candidate['candidate_id']}")
    return manifest, digest
