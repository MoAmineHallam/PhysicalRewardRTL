#!/usr/bin/env python3
"""Fail-closed validation for the frozen external RTLLM slice package."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from common import CATEGORIES, canonical_json_bytes, load_json, selection_key, sha256_bytes, sha256_file


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def validate_package_lock(root: Path) -> None:
    manifest_path = root / "package_manifest.json"
    digest_path = root / "package_manifest.sha256"
    if not manifest_path.is_file() or not digest_path.is_file():
        fail("package lock is missing")
    manifest = load_json(manifest_path)
    actual_digest = sha256_bytes(canonical_json_bytes(manifest))
    expected_digest = digest_path.read_text(encoding="ascii").strip().lower()
    if actual_digest != expected_digest:
        fail(f"package manifest digest mismatch: {actual_digest} != {expected_digest}")
    declared = {row["path"]: row for row in manifest["files"]}
    actual_paths = set()
    for path in root.rglob("*"):
        if not path.is_file() or path.name in {"package_manifest.json", "package_manifest.sha256"}:
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        actual_paths.add(path.relative_to(root).as_posix())
    if actual_paths != set(declared):
        fail(f"package file set changed: missing={sorted(set(declared)-actual_paths)} extra={sorted(actual_paths-set(declared))}")
    for rel, row in declared.items():
        path = root / rel
        if sha256_file(path) != row["sha256"] or path.stat().st_size != row["bytes"]:
            fail(f"package file changed: {rel}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--skip-package-lock", action="store_true")
    args = parser.parse_args()
    root = args.package_root.resolve()
    pin = load_json(root / "upstream_pin.json")
    policy = load_json(root / "selection_policy.json")
    audit = load_json(root / "audit_manifest.json")
    preflight = load_json(root / "reference_preflight.json")
    contamination = load_json(root / "contamination_report.json")
    selection = load_json(root / "selection_manifest.json")
    if pin["commit"] != "e67f150603f52d6abf208ed0e97bd77a95b1ee34":
        fail("unexpected RTLLM commit")
    if audit.get("status") != "PASS" or audit.get("task_count") != 50:
        fail("static audit invariant")
    if preflight.get("status") != "PASS" or contamination.get("status") != "PASS":
        fail("preflight/contamination status")
    manifest_digest = sha256_bytes(canonical_json_bytes(selection))
    frozen_digest = (root / "selection_manifest.sha256").read_text(encoding="ascii").strip().lower()
    if manifest_digest != frozen_digest:
        fail("selection manifest digest")
    selected = selection["selected_tasks"]
    counts = Counter(task["category"] for task in selected)
    if len(selected) != policy["total_tasks"]:
        fail("selected task count")
    if any(counts[category] != policy["tasks_per_category"] for category in CATEGORIES):
        fail(f"category balance: {dict(counts)}")
    ledger_by_category = {category: [] for category in CATEGORIES}
    for row in selection["eligibility_ledger"]:
        expected_key = selection_key(policy, row["category"], row["task_id"])
        if row["selection_key"] != expected_key:
            fail(f"selection key mismatch for {row['task_id']}")
        if row["eligible"]:
            ledger_by_category[row["category"]].append(row)
    expected_ids = set()
    for category in CATEGORIES:
        ranked = sorted(ledger_by_category[category], key=lambda row: (row["selection_key"], row["task_id"]))
        expected_ids.update(row["task_id"] for row in ranked[: policy["tasks_per_category"]])
    selected_ids = {task["task_id"] for task in selected}
    if selected_ids != expected_ids:
        fail(f"selection is not deterministic expected={sorted(expected_ids)} got={sorted(selected_ids)}")
    expected_task_files = set()
    for task in selected:
        task_dir = root / "tasks" / Path(task["task_id"])
        prompt = task_dir / task["prompt"]["path"]
        oracle = task_dir / task["oracle"]["path"]
        metadata = task_dir / "task.json"
        for path, digest in ((prompt, task["prompt"]["sha256"]), (oracle, task["oracle"]["sha256"])):
            if not path.is_file() or sha256_file(path) != digest:
                fail(f"materialized task file mismatch: {path}")
        if load_json(metadata) != task:
            fail(f"task metadata mismatch: {task['task_id']}")
        expected_task_files.update(
            path.relative_to(root).as_posix() for path in (prompt, oracle, metadata)
        )
        if task["upstream_reference"]["copied_into_package"]:
            fail(f"reference exposure for {task['task_id']}")
    actual_task_files = {
        path.relative_to(root).as_posix() for path in (root / "tasks").rglob("*") if path.is_file()
    }
    if actual_task_files != expected_task_files:
        fail(f"unexpected task artifacts: {sorted(actual_task_files - expected_task_files)}")
    forbidden_names = ("candidate", "vivado", "timing_report", "power_report", "result.json")
    for path in root.rglob("*"):
        if path.is_file() and any(token in path.name.lower() for token in forbidden_names):
            fail(f"forbidden generated/outcome artifact in protocol package: {path.relative_to(root)}")
        if path.is_file() and path.name.lower().startswith(("verified", "reference")) and path.suffix.lower() in {".v", ".sv"}:
            fail(f"upstream reference RTL copied into package: {path.relative_to(root)}")
    if args.repo_root:
        repo_root = args.repo_root.resolve()
        for row in contamination["source_files"]:
            path = repo_root / row["path"]
            if not path.is_file() or sha256_file(path) != row["sha256"]:
                fail(f"contamination source changed since freeze: {row['path']}")
    if not args.skip_package_lock:
        validate_package_lock(root)
    print(
        f"PASS external_rtllm_slice_v1 tasks={len(selected)} balanced=2x4 "
        f"selection_manifest_sha256={manifest_digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
