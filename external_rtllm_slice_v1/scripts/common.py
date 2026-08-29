#!/usr/bin/env python3
"""Shared deterministic helpers for the frozen RTLLM slice."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable


CATEGORIES = ("Arithmetic", "Control", "Memory", "Miscellaneous")
RESET_NAME_RE = re.compile(r"(?i)(?:^|_)(?:rst|reset)(?:_?n)?(?:$|_)")
MODULE_RE = re.compile(r"(?m)^\s*module\s+([A-Za-z_]\w*)")
EXPECTED_MODULE_RE = re.compile(
    r"(?is)module\s*name\s*:\s*(?:\r?\n\s*)?([A-Za-z_]\w*)"
)
ALWAYS_SENS_RE = re.compile(r"(?is)\balways(?:_ff)?\s*@?\s*\(([^)]*)\)")
EDGE_RE = re.compile(r"(?i)\b(?:pos|neg)edge\s+([A-Za-z_]\w*)")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def strip_verilog_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\r\n]*", " ", text)


def normalize_prompt(text: str) -> str:
    return " ".join(text.lower().split())


def normalize_verilog(text: str) -> str:
    text = strip_verilog_comments(text).lower()
    text = re.sub(r"\bmodule\s+[a-z_]\w*", "module <top>", text, count=1)
    return re.sub(r"\s+", "", text)


def expected_module(description: str) -> str | None:
    match = EXPECTED_MODULE_RE.search(description)
    return match.group(1) if match else None


def task_id(root: Path, task_dir: Path) -> str:
    return task_dir.relative_to(root).as_posix()


def discover_tasks(root: Path) -> list[Path]:
    tasks = sorted(p.parent for p in root.rglob("design_description.txt"))
    return [p for p in tasks if p.relative_to(root).parts and p.relative_to(root).parts[0] in CATEGORIES]


def git_head(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.stdout.strip().lower() if proc.returncode == 0 else None


def verify_upstream_identity(root: Path, pin: dict[str, Any]) -> dict[str, Any]:
    if not root.is_dir():
        raise ValueError(f"upstream root does not exist: {root}")
    head = git_head(root)
    dirname_commit = root.name.rsplit("-", 1)[-1].lower() if "-" in root.name else ""
    commit = pin["commit"].lower()
    identity_mode = None
    if head == commit:
        identity_mode = "git_head"
    elif dirname_commit == commit:
        identity_mode = "github_archive_directory"
    if identity_mode is None:
        raise ValueError(
            f"upstream identity is not pinned commit {commit}: git_head={head!r}, directory={root.name!r}"
        )
    checks = {
        "File_list.md": pin["file_list_sha256"],
        "LICENSE": pin["license_sha256"],
    }
    for rel, expected in checks.items():
        actual = sha256_file(root / rel)
        if actual != expected:
            raise ValueError(f"upstream {rel} hash mismatch: {actual} != {expected}")
    return {"mode": identity_mode, "commit": commit, "git_head": head}


def sensitivity_audit(reference_text: str) -> dict[str, Any]:
    clean = strip_verilog_comments(reference_text)
    edge_signals: list[str] = []
    mixed: list[str] = []
    sensitivities = ALWAYS_SENS_RE.findall(clean)
    for sensitivity in sensitivities:
        edges = EDGE_RE.findall(sensitivity)
        edge_signals.extend(edges)
        if edges:
            residue = EDGE_RE.sub("", sensitivity)
            residue = re.sub(r"(?i)\bor\b|,|\s|\(|\)", "", residue)
            if residue:
                mixed.append(sensitivity.strip())
    unique_edges = sorted(set(edge_signals), key=str.lower)
    clocks = sorted((s for s in unique_edges if not RESET_NAME_RE.search(s)), key=str.lower)
    resets = sorted((s for s in unique_edges if RESET_NAME_RE.search(s)), key=str.lower)
    return {
        "sensitivities": sensitivities,
        "edge_signals": unique_edges,
        "clock_signals": clocks,
        "reset_signals": resets,
        "mixed_edge_level_sensitivities": mixed,
    }


def all_text_values(value: Any) -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(item, str):
                yield str(key), item
            else:
                yield from all_text_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_text_values(item)


def selection_key(policy: dict[str, Any], category: str, identifier: str) -> str:
    payload = f"{policy['selection_salt']}|{category}|{identifier}".encode("utf-8")
    return sha256_bytes(payload)
