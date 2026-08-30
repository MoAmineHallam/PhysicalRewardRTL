#!/usr/bin/env python3
"""Immutable identities and raw-hash checks for candidate pilot V7."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
V1 = ROOT / "timing_closure_gate_v1"
V7 = ROOT / "timing_closure_gate_v7"
V1_MANIFEST = V1 / "manifest.json"
V7_MANIFEST = V7 / "manifest.json"
V7_ATTESTATION = V7 / "stability_campaign_001" / "stability_attestation.json"
BASELINE = V7 / "dependency_baseline.json"
PACKAGE_MANIFEST = HERE / "manifest.json"
PACKAGE_SHA = HERE / "manifest.sha256"

V1_MANIFEST_SHA = "2e0674f96c57be3864a6fab7683b0edc76f732762f78547d5e6a3e8efc17e194"
V7_MANIFEST_SHA = "c2bfb67f49584787cf23668689e5fa86ed4165e5510c9e4ea2f779e8de387f0b"
V7_ATTESTATION_SHA = "951b4b577fea68cba2d4478ae6022d7be8eec5e373f306d7c89c008c34f929b1"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False) + "\n").encode("utf-8")


def atomic_json(path: Path, value: Any, *, replace: bool = False) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not replace and path.exists():
        raise RuntimeError(f"refusing to overwrite artifact: {path}")
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}")
    temporary.write_bytes(canonical_json_bytes(value))
    if not replace and path.exists():
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"artifact appeared during publication: {path}")
    os.replace(temporary, path)


def expected_sha_line(path: Path) -> str:
    fields = Path(path).read_text(encoding="ascii").strip().split()
    if len(fields) != 2:
        raise RuntimeError(f"malformed SHA-256 line: {path}")
    return fields[0]


def verify_v7_pass() -> dict[str, Any]:
    if V7_ATTESTATION_SHA.startswith("__"):
        raise RuntimeError("V7 attestation digest has not been frozen")
    if sha256_file(V7_ATTESTATION) != V7_ATTESTATION_SHA:
        raise RuntimeError("V7 stability attestation hash mismatch")
    sha_path = V7_ATTESTATION.with_name("stability_attestation.sha256")
    if expected_sha_line(sha_path) != V7_ATTESTATION_SHA:
        raise RuntimeError("V7 stability SHA file mismatch")
    value = read_json(V7_ATTESTATION)
    rows = value.get("runs", [])
    if not (value.get("study_id") == "timing_closure_gate_v7"
            and value.get("verdict") == "PASS"
            and value.get("contains_study2_rtl") is False
            and value.get("vivado_version") == "2026.1"
            and value.get("target_part") == "xc7z020clg400-1"
            and value.get("explicit_tempdir") is True
            and len(rows) == 40
            and all(row.get("valid_measurement") is True for row in rows)):
        raise RuntimeError("V7 stability attestation is not the frozen 40/40 PASS")
    return value


def verify_inputs() -> tuple[dict[str, Any], str]:
    if sha256_file(V1_MANIFEST) != V1_MANIFEST_SHA:
        raise RuntimeError("V1 candidate manifest hash mismatch")
    if expected_sha_line(V1 / "manifest.sha256") != V1_MANIFEST_SHA:
        raise RuntimeError("V1 manifest SHA file mismatch")
    if sha256_file(V7_MANIFEST) != V7_MANIFEST_SHA:
        raise RuntimeError("V7 package manifest hash mismatch")
    if expected_sha_line(V7 / "manifest.sha256") != V7_MANIFEST_SHA:
        raise RuntimeError("V7 package SHA file mismatch")
    verify_v7_pass()
    manifest = read_json(V1_MANIFEST)
    candidates = manifest.get("candidates", [])
    if len(candidates) != 10:
        raise RuntimeError("V1 manifest no longer contains exactly ten candidates")
    for candidate in candidates:
        source = ROOT / candidate["materialized_path"]
        if sha256_file(source) != candidate["emitted_sha256"]:
            raise RuntimeError(
                f"candidate RTL hash mismatch: {candidate['candidate_id']}")
    closure = V1 / "closure_synth.tcl"
    expected = manifest["dependency_sha256"][
        "timing_closure_gate_v1/closure_synth.tcl"]
    if sha256_file(closure) != expected:
        raise RuntimeError("closure Tcl hash mismatch")
    return manifest, V1_MANIFEST_SHA


def verify_package() -> str:
    expected = expected_sha_line(PACKAGE_SHA)
    actual = sha256_file(PACKAGE_MANIFEST)
    if actual != expected:
        raise RuntimeError(f"candidate package manifest mismatch: {actual}")
    manifest = read_json(PACKAGE_MANIFEST)
    for row in manifest.get("files", []):
        path = ROOT / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256_raw"]:
            raise RuntimeError(
                f"candidate package dependency changed: {row['path']}")
    verify_inputs()
    return actual
