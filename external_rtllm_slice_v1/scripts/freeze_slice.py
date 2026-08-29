#!/usr/bin/env python3
"""Deterministically select and materialize the balanced eight-task slice."""

from __future__ import annotations

import argparse
import shutil
from collections import Counter
from pathlib import Path

from common import (
    CATEGORIES,
    canonical_json_bytes,
    load_json,
    selection_key,
    sha256_bytes,
    sha256_file,
    verify_upstream_identity,
    write_json,
)


def indexed(items: list[dict]) -> dict[str, dict]:
    result = {item["task_id"]: item for item in items}
    if len(result) != len(items):
        raise ValueError("duplicate task_id in frozen input")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    package_root = args.package_root.resolve()
    upstream = args.upstream.resolve()
    pin = load_json(package_root / "upstream_pin.json")
    policy = load_json(package_root / "selection_policy.json")
    identity = verify_upstream_identity(upstream, pin)
    audit = load_json(package_root / "audit_manifest.json")
    preflight = load_json(package_root / "reference_preflight.json")
    contamination = load_json(package_root / "contamination_report.json")
    if audit.get("status") != "PASS" or audit.get("task_count") != policy["eligibility"]["required_task_count"]:
        raise SystemExit("FAIL: invalid static audit")
    if preflight.get("status") != "PASS" or contamination.get("status") != "PASS":
        raise SystemExit("FAIL: missing preflight or contamination audit")
    preflight_by_id = indexed(preflight["results"])
    contamination_by_id = indexed(contamination["tasks"])
    eligible_by_category: dict[str, list[dict]] = {category: [] for category in CATEGORIES}
    eligibility_rows = []
    for task in audit["tasks"]:
        task_identifier = task["task_id"]
        reference_result = preflight_by_id.get(task_identifier)
        contamination_result = contamination_by_id[task_identifier]
        eligible = bool(
            task["static_eligible"]
            and reference_result
            and reference_result["status"] == "PASS"
            and contamination_result["clean"]
        )
        key = selection_key(policy, task["category"], task_identifier)
        row = {
            "task_id": task_identifier,
            "category": task["category"],
            "eligible": eligible,
            "selection_key": key,
            "static_eligible": task["static_eligible"],
            "reference_preflight": reference_result["status"] if reference_result else "NOT_RUN",
            "contamination_clean": contamination_result["clean"],
        }
        eligibility_rows.append(row)
        if eligible:
            eligible_by_category[task["category"]].append(row)
    chosen = []
    for category in CATEGORIES:
        ranked = sorted(eligible_by_category[category], key=lambda row: (row["selection_key"], row["task_id"]))
        if len(ranked) < policy["tasks_per_category"]:
            raise SystemExit(f"FAIL: category {category} has only {len(ranked)} eligible tasks")
        chosen.extend(ranked[: policy["tasks_per_category"]])
    chosen = sorted(chosen, key=lambda row: (CATEGORIES.index(row["category"]), row["selection_key"]))
    audit_by_id = indexed(audit["tasks"])
    tasks_root = package_root / "tasks"
    manifest_tasks = []
    for rank, chosen_row in enumerate(chosen, 1):
        task = audit_by_id[chosen_row["task_id"]]
        source_description = upstream / task["description"]["path"]
        source_testbench = upstream / task["testbench"]["path"]
        source_reference = upstream / task["reference"]["path"]
        if sha256_file(source_description) != task["description"]["sha256"]:
            raise SystemExit(f"FAIL: description changed for {task['task_id']}")
        if sha256_file(source_testbench) != task["testbench"]["sha256"]:
            raise SystemExit(f"FAIL: testbench changed for {task['task_id']}")
        if sha256_file(source_reference) != task["reference"]["sha256"]:
            raise SystemExit(f"FAIL: reference changed for {task['task_id']}")
        destination = tasks_root.joinpath(*Path(task["task_id"]).parts)
        oracle_dir = destination / "oracle"
        oracle_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = destination / "prompt.txt"
        testbench_path = oracle_dir / "testbench.v"
        shutil.copyfile(source_description, prompt_path)
        shutil.copyfile(source_testbench, testbench_path)
        task_metadata = {
            "schema_version": 1,
            "task_id": task["task_id"],
            "category": task["category"],
            "expected_module": task["expected_module"],
            "clock_signals": task["reference"]["clock_signals"],
            "reset_signals": task["reference"]["reset_signals"],
            "selection_key": chosen_row["selection_key"],
            "prompt": {"path": "prompt.txt", "sha256": sha256_file(prompt_path)},
            "oracle": {"path": "oracle/testbench.v", "sha256": sha256_file(testbench_path)},
            "upstream_reference": {
                "copied_into_package": False,
                "path_at_pinned_commit": task["reference"]["path"],
                "sha256": task["reference"]["sha256"],
            },
        }
        write_json(destination / "task.json", task_metadata)
        manifest_tasks.append(task_metadata)
    shutil.copyfile(upstream / "LICENSE", package_root / "UPSTREAM_LICENSE.txt")
    category_counts = Counter(task["category"] for task in manifest_tasks)
    manifest = {
        "schema_version": 1,
        "status": "FROZEN",
        "policy_id": policy["policy_id"],
        "upstream": identity,
        "task_count": len(manifest_tasks),
        "category_counts": dict(sorted(category_counts.items())),
        "eligible_counts": {category: len(eligible_by_category[category]) for category in CATEGORIES},
        "selection_rule": policy["selection_key"],
        "outcome_independence": policy["outcome_independence"],
        "selected_tasks": manifest_tasks,
        "eligibility_ledger": sorted(eligibility_rows, key=lambda row: row["task_id"]),
    }
    if len(manifest_tasks) != policy["total_tasks"] or any(
        category_counts[category] != policy["tasks_per_category"] for category in CATEGORIES
    ):
        raise SystemExit("FAIL: balanced selection invariant violated")
    manifest_path = package_root / "selection_manifest.json"
    write_json(manifest_path, manifest)
    digest = sha256_bytes(canonical_json_bytes(manifest))
    (package_root / "selection_manifest.sha256").write_text(digest + "\n", encoding="ascii")
    print(f"PASS frozen tasks={len(manifest_tasks)} selection_manifest_sha256={digest}")
    for task in manifest_tasks:
        print(f"  {task['category']}: {task['task_id']} key={task['selection_key']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
