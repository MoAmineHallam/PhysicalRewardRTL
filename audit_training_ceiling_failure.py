#!/usr/bin/env python3
"""Create a reproducible audit of a training run that hit its group ceiling.

The output deliberately contains counts and hashes, never candidate RTL.  It is
used to preserve the failed revision-5 correctness run before revision 6 starts
from update zero under the already-frozen crash policy.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from collections import Counter


class AuditError(RuntimeError):
    pass


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: str, root: str) -> dict:
    return {
        "path": os.path.relpath(os.path.abspath(path), root).replace(os.sep, "/"),
        "bytes": os.path.getsize(path),
        "sha256_raw": sha256_file(path),
    }


def directory_manifest(path: str) -> dict:
    entries = []
    for dirpath, _dirs, filenames in os.walk(path):
        for filename in sorted(filenames):
            full = os.path.join(dirpath, filename)
            rel = os.path.relpath(full, path).replace(os.sep, "/")
            entries.append((rel, sha256_file(full), os.path.getsize(full)))
    digest = hashlib.sha256()
    for rel, file_hash, _size in sorted(entries):
        digest.update(rel.encode("utf-8") + b"\0" + file_hash.encode("ascii") + b"\n")
    return {
        "sha256_raw_file_manifest": digest.hexdigest(),
        "n_files": len(entries),
        "files": [
            {"path": rel, "sha256_raw": file_hash, "bytes": size}
            for rel, file_hash, size in sorted(entries)
        ],
    }


def read_object(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, ValueError) as exc:
        raise AuditError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{path} is not a JSON object")
    return value


def audit_group_log(path: str, expected_groups: int, expected_updates: int,
                    bin_size: int) -> dict:
    rows = groups = updates = flat_groups = 0
    last_update_group = None
    update_ids = []
    update_groups = []
    bins = Counter()
    current_group = None
    group_rows = []

    def finish_group(group_index: int, group: list[dict]) -> None:
        nonlocal groups, updates, flat_groups, last_update_group
        if len(group) != 8:
            raise AuditError(f"group {group_index} has {len(group)} rows, expected 8")
        designs = {row.get("design") for row in group}
        flats = {row.get("flat") for row in group}
        update_values = {row.get("update") for row in group}
        if len(designs) != 1 or None in designs:
            raise AuditError(f"group {group_index} mixes or omits designs")
        if len(flats) != 1 or len(update_values) != 1:
            raise AuditError(f"group {group_index} is internally inconsistent")
        flat = flats.pop()
        update = update_values.pop()
        if not isinstance(flat, bool):
            raise AuditError(f"group {group_index} has non-boolean flat flag")
        groups += 1
        if flat:
            flat_groups += 1
            if update is not None:
                raise AuditError(f"flat group {group_index} records update {update}")
        else:
            updates += 1
            last_update_group = group_index
            update_ids.append(update)
            update_groups.append(group_index)
            bins[(group_index - 1) // bin_size] += 1

    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise AuditError(f"invalid JSON at {path}:{line_number}: {exc}") from exc
            group_index = row.get("group_index")
            if not isinstance(group_index, int):
                raise AuditError(f"missing integer group_index at {path}:{line_number}")
            if current_group is None:
                current_group = group_index
            if group_index != current_group:
                finish_group(current_group, group_rows)
                if group_index != current_group + 1:
                    raise AuditError(f"group sequence jumps {current_group} -> {group_index}")
                current_group, group_rows = group_index, []
            group_rows.append(row)
            rows += 1
    if current_group is not None:
        finish_group(current_group, group_rows)

    if groups != expected_groups or rows != expected_groups * 8:
        raise AuditError(f"observed {groups} groups/{rows} rows; expected {expected_groups}/{expected_groups * 8}")
    if updates != expected_updates or update_ids != list(range(1, expected_updates + 1)):
        raise AuditError("optimizer updates do not equal the exact sequence 1..expected_updates")

    bin_rows = []
    for start in range(1, expected_groups + 1, bin_size):
        end = min(start + bin_size - 1, expected_groups)
        count = bins[(start - 1) // bin_size]
        bin_rows.append({
            "groups": [start, end],
            "updates": count,
            "nonflat_rate": count / (end - start + 1),
        })
    late_windows = {}
    for window in (500, 1000, 1500):
        start = max(1, groups - window + 1)
        observed = sum(group_index >= start for group_index in update_groups)
        denominator = groups - start + 1
        late_windows[str(window)] = {
            "groups": [start, groups],
            "updates": observed,
            "nonflat_rate": observed / denominator,
        }
    return {
        "rows": rows,
        "attempted_groups": groups,
        "optimizer_updates": updates,
        "flat_groups": flat_groups,
        "flat_rate": flat_groups / groups,
        "last_update_group": last_update_group,
        "trailing_flat_groups": groups - last_update_group,
        "late_windows": late_windows,
        "update_ids_are_exactly_1_through_n": True,
        f"bins_{bin_size}_groups": bin_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--external", nargs="*", default=[])
    parser.add_argument("--identity", nargs="*", default=[])
    parser.add_argument("--out", required=True)
    parser.add_argument("--expected-groups", type=int, default=4500)
    parser.add_argument("--expected-updates", type=int, default=215)
    parser.add_argument("--target-updates", type=int, default=276)
    parser.add_argument("--bin-size", type=int, default=250)
    args = parser.parse_args()

    root = os.path.abspath(os.getcwd())
    run_dir = os.path.abspath(args.run_dir)
    config = read_object(os.path.join(run_dir, "run_config.json"))
    summary = read_object(os.path.join(run_dir, "run_summary.json"))
    groups = audit_group_log(
        os.path.join(run_dir, "group_log.jsonl"), args.expected_groups,
        args.expected_updates, args.bin_size)

    expected_config = {
        "reward": "correctness", "seed": 1, "max_groups": args.expected_groups,
        "steps": args.expected_groups, "max_updates": args.target_updates,
        "group": 8, "dtype": "torch.float16",
    }
    mismatches = {
        key: {"expected": value, "observed": config.get(key)}
        for key, value in expected_config.items() if config.get(key) != value
    }
    if mismatches:
        raise AuditError(f"run_config mismatch: {mismatches}")
    for key, value in {
        "attempted_groups": args.expected_groups,
        "updates": args.expected_updates,
        "flat_groups": args.expected_groups - args.expected_updates,
        "ended": "steps exhausted",
    }.items():
        if summary.get(key) != value:
            raise AuditError(f"run_summary[{key!r}]={summary.get(key)!r}, expected {value!r}")
    if summary.get("checkpoints") != [138] or summary.get("missed_checkpoints") != [args.target_updates]:
        raise AuditError("run_summary checkpoint accounting is not exactly [138] present/[276] missed")

    present = [u for u in (138, args.target_updates)
               if os.path.isdir(os.path.join(run_dir, f"upd_{u}"))]
    if present != [138]:
        raise AuditError(f"expected only checkpoint 138, observed {present}")

    artifact = {
        "schema": "training-ceiling-failure-audit-v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": "revision-5 correctness seed-1 training feasibility only; no sealed efficacy output",
        "disposition": "preserved failure; never resumed, merged, or treated as an endpoint",
        "expected": expected_config,
        "run_summary": summary,
        "group_log_audit": groups,
        "checkpoints_present": present,
        "checkpoints_absent": [args.target_updates],
        "run_directory_manifest": directory_manifest(run_dir),
        "external_files": [file_record(path, root) for path in args.external],
        "launch_identity_files": [file_record(path, root) for path in args.identity],
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(artifact, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({
        "out": args.out,
        "attempted_groups": groups["attempted_groups"],
        "optimizer_updates": groups["optimizer_updates"],
        "flat_groups": groups["flat_groups"],
        "last_update_group": groups["last_update_group"],
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except AuditError as exc:
        raise SystemExit(f"FAIL: {exc}")
