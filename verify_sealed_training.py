#!/usr/bin/env python3
"""Fail-closed completion audit for all preregistered training arms.

Run this after the five GPU jobs and before generating a single sealed-policy
sample.  It checks every run configuration, checkpoint, summary, and group log
against the fixed protocol and writes a machine-readable audit artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from typing import Dict, Optional, Sequence


EXPECTED = {
    "grpo_rf_s1": {"reward": "rf_struct", "seed": 1, "max_groups": 2000},
    "grpo_rf_s2": {"reward": "rf_struct", "seed": 2, "max_groups": 2000},
    "grpo_mlp_s1": {"reward": "mlp", "seed": 1, "max_groups": 2000},
    "grpo_mlp_s2": {"reward": "mlp", "seed": 2, "max_groups": 2000},
    "grpo_corr_s1": {"reward": "correctness", "seed": 1, "max_groups": 4500},
}
TARGET_UPDATES = 276
CHECKPOINTS = [138, 276]


class TrainingAuditError(RuntimeError):
    pass


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        raw = handle.read()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def read_json(path: str) -> dict:
    try:
        value = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise TrainingAuditError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TrainingAuditError(f"{path} is not a JSON object")
    return value


def same_float(actual, expected, label: str) -> None:
    try:
        good = math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=1e-12)
    except (TypeError, ValueError):
        good = False
    if not good:
        raise TrainingAuditError(f"{label}: expected {expected}, got {actual!r}")


def audit_group_log(path: str) -> dict:
    groups: Dict[int, list] = {}
    update_to_group = {}
    rows = 0
    with open(path, encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise TrainingAuditError(f"malformed JSON at {path}:{lineno}") from exc
            group = row.get("group_index") if isinstance(row, dict) else None
            if not isinstance(group, int) or group <= 0:
                raise TrainingAuditError(f"bad group index at {path}:{lineno}")
            groups.setdefault(group, []).append(row)
            rows += 1
    if not groups or any(len(value) != 8 for value in groups.values()):
        raise TrainingAuditError(f"{path} is empty or has a non-eight-candidate group")
    if set(groups) != set(range(1, len(groups) + 1)):
        raise TrainingAuditError(f"{path} group indices are not consecutive from one")
    flat_groups = 0
    for group_index, group_rows in groups.items():
        designs = {row.get("design") for row in group_rows}
        flat_values = {row.get("flat") for row in group_rows}
        update_values = {row.get("update") for row in group_rows}
        if len(designs) != 1 or None in designs:
            raise TrainingAuditError(f"group {group_index} in {path} mixes designs")
        if len(flat_values) != 1 or len(update_values) != 1:
            raise TrainingAuditError(f"group {group_index} in {path} is internally inconsistent")
        flat = flat_values.pop()
        update = update_values.pop()
        if flat is True:
            flat_groups += 1
            if update is not None:
                raise TrainingAuditError(f"flat group {group_index} in {path} has an update")
        elif flat is False:
            if not isinstance(update, int) or update <= 0:
                raise TrainingAuditError(f"non-flat group {group_index} lacks an update")
            if update in update_to_group:
                raise TrainingAuditError(f"update {update} appears in multiple groups in {path}")
            update_to_group[update] = group_index
        else:
            raise TrainingAuditError(f"group {group_index} lacks a Boolean flat flag")
    updates = set(update_to_group)
    if updates != set(range(1, TARGET_UPDATES + 1)):
        raise TrainingAuditError(f"{path} does not contain exactly updates 1..276")
    return {"path": os.path.abspath(path), "sha256": sha256_file(path),
            "rows": rows, "groups": len(groups), "updates": len(updates),
            "flat_groups": flat_groups}


def audit_run(root: str, name: str, expected: dict) -> dict:
    directory = os.path.join(root, name)
    if not os.path.isdir(directory):
        raise TrainingAuditError(f"missing training directory: {directory}")
    config = read_json(os.path.join(directory, "run_config.json"))
    summary = read_json(os.path.join(directory, "run_summary.json"))
    exact = {
        "reward": expected["reward"], "seed": expected["seed"],
        "group": 8, "max_tokens": 1536, "max_updates": TARGET_UPDATES,
        "max_groups": expected["max_groups"], "save_at_updates": CHECKPOINTS,
    }
    for key, wanted in exact.items():
        if config.get(key) != wanted:
            raise TrainingAuditError(
                f"{name} run_config {key}: expected {wanted!r}, got {config.get(key)!r}")
    same_float(config.get("temp"), 1.0, f"{name} temperature")
    same_float(config.get("lr"), 1e-5, f"{name} learning rate")
    same_float(config.get("kl_coef"), 0.1, f"{name} KL coefficient")
    same_float(config.get("incorrect_reward"), 0.0, f"{name} incorrect reward")
    if summary.get("updates") != TARGET_UPDATES:
        raise TrainingAuditError(f"{name} stopped at {summary.get('updates')} updates")
    if summary.get("ended") != "target updates reached (276)":
        raise TrainingAuditError(f"{name} ended unexpectedly: {summary.get('ended')}")
    if summary.get("checkpoints") != CHECKPOINTS or summary.get("missed_checkpoints") != []:
        raise TrainingAuditError(f"{name} checkpoint summary is incomplete")
    for update in CHECKPOINTS:
        checkpoint = os.path.join(directory, f"upd_{update}")
        if not os.path.isdir(checkpoint) or not os.listdir(checkpoint):
            raise TrainingAuditError(f"missing {name} update-{update} checkpoint")
    group = audit_group_log(os.path.join(directory, "group_log.jsonl"))
    if summary.get("attempted_groups") != group["groups"]:
        raise TrainingAuditError(f"{name} summary/group-log attempted counts disagree")
    if summary.get("flat_groups") != group["flat_groups"]:
        raise TrainingAuditError(f"{name} summary/group-log flat counts disagree")
    if group["groups"] > expected["max_groups"]:
        raise TrainingAuditError(f"{name} exceeded its attempted-group ceiling")
    return {
        "name": name, "directory": os.path.abspath(directory),
        "reward": expected["reward"], "seed": expected["seed"],
        "attempted_groups": summary.get("attempted_groups"),
        "flat_groups": summary.get("flat_groups"),
        "run_config_sha256": sha256_file(os.path.join(directory, "run_config.json")),
        "run_summary_sha256": sha256_file(os.path.join(directory, "run_summary.json")),
        "group_log": group,
    }


def run(root: str, output: str) -> dict:
    records = [audit_run(root, name, expected)
               for name, expected in EXPECTED.items()]
    result = {"schema": "sealed_training_audit/1", "complete": True,
              "target_updates": TARGET_UPDATES,
              "checkpoints": CHECKPOINTS, "runs": records}
    with open(output, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=1)
        handle.write("\n")
    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="sealed_training_audit.json")
    args = ap.parse_args(argv)
    try:
        result = run(args.root, args.out)
    except TrainingAuditError as exc:
        print(f"sealed training audit error: {exc}", file=sys.stderr)
        return 2
    print(f"PASS: {len(result['runs'])} preregistered training runs complete")
    print(f"audit -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
