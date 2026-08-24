#!/usr/bin/env python3
"""Audit and materialize the RF candidates that actually reached the reward.

This is the Study 2 pre-open gate.  It deliberately does not replace the
Study 1 all-candidate gate.  Correct candidates must have reached the RF
reward with complete logged metadata; incorrect candidates must have zero
reward and are counted, but are not part of the RF implementation contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable

from canonicalize import (
    Unsupported,
    canon_hash,
    canonicalize,
    struct_feature_dict,
    trace_equal,
    verify_contract,
)


EXPECTED_CANDIDATES_PER_GROUP = 8


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def normalized_rtl(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def safe_name(design: str, digest: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", design).strip("._") or "unknown"
    return f"rfstudy2__{stem}__{digest[:16]}.sv"


def load_preregistration(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    study = data.get("study2", {})
    if study.get("study_id") != "rf_reward_eligible_study2":
        raise ValueError("preregistration has the wrong Study 2 identifier")
    return data


def load_rows(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for path in paths:
        source_rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                row["_source_file"] = path.as_posix()
                row["_source_line"] = line_no
                source_rows.append(row)
                rows.append(row)
        sources.append(
            {
                "path": path.as_posix(),
                "sha256": sha256_file(path),
                "rows": len(source_rows),
            }
        )
    return rows, sources


def validate_group_shape(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    groups: dict[tuple[str, Any], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row.get("_source_file")), row.get("group_index"))].append(row)
    for (source, group), members in sorted(groups.items(), key=lambda item: str(item[0])):
        ids = sorted(m.get("cand") for m in members)
        if len(members) != EXPECTED_CANDIDATES_PER_GROUP or ids != list(
            range(EXPECTED_CANDIDATES_PER_GROUP)
        ):
            errors.append(
                f"{source}: group {group!r} has {len(members)} candidates with ids {ids!r}"
            )
    return errors


def classify_row(row: dict[str, Any]) -> tuple[bool, str, list[str]]:
    """Return (reward_eligible, exclusion_reason, validation_errors)."""
    errors: list[str] = []
    rtl = normalized_rtl(row.get("rtl"))
    correct = row.get("correct") is True
    gate = row.get("gate")
    reward = row.get("reward")
    features = row.get("struct_features")
    canon_hash = row.get("canon_hash")

    if correct:
        if not rtl:
            errors.append("correct row has empty RTL")
        if gate != "ok":
            errors.append(f"correct row has gate={gate!r}, expected 'ok'")
        if not isinstance(features, dict):
            errors.append("correct row lacks structural-feature metadata")
        if not isinstance(canon_hash, str) or not canon_hash:
            errors.append("correct row lacks canonical hash")
        if not isinstance(reward, (int, float)) or not math.isfinite(float(reward)) or reward <= 0:
            errors.append(f"correct row has non-positive/non-finite reward {reward!r}")
        return not errors, "", errors

    if isinstance(reward, bool) or not isinstance(reward, (int, float)) or float(reward) != 0.0:
        errors.append(f"non-correct row has nonzero/non-numeric reward {reward!r}")
    if not rtl:
        return False, "no_module", errors
    return False, str(gate or "oracle_incorrect"), errors


def _jsonable_failure(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def audit(
    log_paths: list[Path],
    prereg_path: Path,
    output_dir: Path,
    manifest_path: Path,
    contract_path: Path,
    *,
    verify_fn: Callable[[str], dict[str, Any]] = verify_contract,
    canonicalize_fn: Callable[[str], str] = canonicalize,
    features_fn: Callable[[str], dict[str, Any]] = struct_feature_dict,
    trace_fn: Callable[..., Any] = trace_equal,
) -> dict[str, Any]:
    for target in (output_dir, manifest_path, contract_path):
        if target.exists():
            raise FileExistsError(f"refusing to mix Study 2 artifacts: {target} already exists")

    prereg = load_preregistration(prereg_path)
    study = prereg["study2"]
    expected_logs = study["training_inputs"]["rf_group_logs"]
    if len(log_paths) != len(expected_logs):
        raise ValueError(f"expected {len(expected_logs)} RF group logs, got {len(log_paths)}")

    rows, sources = load_rows(log_paths)
    expected_hashes = sorted(item["sha256"] for item in expected_logs)
    actual_hashes = sorted(item["sha256"] for item in sources)
    if actual_hashes != expected_hashes:
        raise ValueError(f"RF group-log hashes do not match preregistration: {actual_hashes!r}")

    errors = validate_group_shape(rows)
    gate_counts: Counter[str] = Counter()
    eligible_occurrences: list[dict[str, Any]] = []
    by_rtl: dict[str, list[tuple[dict[str, Any], bool, str]]] = defaultdict(list)
    for row in rows:
        eligible, reason, row_errors = classify_row(row)
        pointer = f"{row['_source_file']}:{row['_source_line']}"
        errors.extend(f"{pointer}: {message}" for message in row_errors)
        gate_counts["reward_eligible" if eligible else f"excluded:{reason}"] += 1
        rtl = normalized_rtl(row.get("rtl"))
        if rtl:
            by_rtl[rtl].append((row, eligible, reason))
        if eligible:
            eligible_occurrences.append(row)

    mixed: list[dict[str, Any]] = []
    eligible_records: list[dict[str, Any]] = []
    for rtl, occurrences in by_rtl.items():
        eligibility = {item[1] for item in occurrences}
        designs = {str(item[0].get("design")) for item in occurrences}
        digest = sha256_bytes(rtl.encode("utf-8"))
        if len(eligibility) != 1 or len(designs) != 1:
            mixed.append(
                {
                    "rtl_sha256": digest,
                    "eligibility": sorted(eligibility),
                    "designs": sorted(designs),
                    "sources": [
                        f"{item[0]['_source_file']}:{item[0]['_source_line']}" for item in occurrences
                    ],
                }
            )
            continue
        if True not in eligibility:
            continue
        first = occurrences[0][0]
        logged_hashes = {item[0].get("canon_hash") for item in occurrences}
        logged_features = {
            json.dumps(item[0].get("struct_features"), sort_keys=True, separators=(",", ":"))
            for item in occurrences
        }
        if len(logged_hashes) != 1 or len(logged_features) != 1:
            errors.append(f"eligible RTL {digest} has inconsistent logged reward metadata")
        filename = safe_name(str(first.get("design")), digest)
        eligible_records.append(
            {
                "filename": filename,
                "design": str(first.get("design")),
                "rtl_sha256": digest,
                "occurrences": len(occurrences),
                "logged_canon_hash": first.get("canon_hash"),
                "logged_struct_features": first.get("struct_features"),
                "sources": [
                    {
                        "file": item[0]["_source_file"],
                        "line": item[0]["_source_line"],
                        "group_index": item[0].get("group_index"),
                        "cand": item[0].get("cand"),
                    }
                    for item in occurrences
                ],
                "_rtl": rtl,
            }
        )

    eligible_records.sort(key=lambda item: (item["design"], item["rtl_sha256"]))
    expected = study["reward_eligible_gate"]["frozen_expected_counts"]
    observed_counts = {
        "total_occurrences": len(rows),
        "nonempty_rtl_occurrences": sum(1 for row in rows if normalized_rtl(row.get("rtl"))),
        "reward_eligible_occurrences": len(eligible_occurrences),
        "reward_eligible_distinct": len(eligible_records),
    }
    for key, expected_value in expected.items():
        if key in observed_counts and observed_counts[key] != expected_value:
            errors.append(f"count {key}={observed_counts[key]}, expected {expected_value}")
    if mixed:
        errors.append(f"{len(mixed)} distinct RTL contents mix eligibility or design identities")

    output_dir.mkdir(parents=True)
    for record in eligible_records:
        rtl = record.pop("_rtl")
        (output_dir / record["filename"]).write_text(rtl + "\n", encoding="utf-8", newline="\n")

    manifest = {
        "schema_version": 1,
        "study_id": study["study_id"],
        "preregistration": {
            "path": prereg_path.as_posix(),
            "sha256": sha256_file(prereg_path),
        },
        "source_logs": sources,
        "counts": observed_counts,
        "gate_counts": dict(sorted(gate_counts.items())),
        "mixed_distinct_rtl": mixed,
        "pre_contract_errors": errors,
        "candidates": eligible_records,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    per_file_by_name: dict[str, Any] = {}
    failure_details: list[dict[str, Any]] = []
    failure_counts: Counter[str] = Counter()
    canonical_groups: dict[str, list[str]] = defaultdict(list)
    for record in eligible_records:
        filename = record["filename"]
        rtl = (output_dir / filename).read_text(encoding="utf-8")
        result: dict[str, Any] = {
            "design": record["design"],
            "rtl_sha256": record["rtl_sha256"],
            "occurrences": record["occurrences"],
            "accepted": False,
        }
        try:
            checked = verify_fn(rtl, backend="lexical")
            if not checked.get("ok"):
                raise Unsupported("canonical contract rejected candidate")
            canon, backend = canonicalize_fn(rtl, backend="lexical")
            if backend != "lexical":
                raise ValueError(f"unexpected canonicalization backend {backend!r}")
            recomputed_hash = canon_hash(canon)
            canonical_sha256 = sha256_bytes(canon.encode("utf-8"))
            recomputed_features = features_fn(canon)
            trace = trace_fn(
                rtl,
                canon,
                record["design"],
                n=int(study["reward_eligible_gate"]["trace_vectors"]),
                seeds=tuple(study["reward_eligible_gate"]["trace_seeds"]),
            )
            result.update(
                {
                    "canonical_hash": recomputed_hash,
                    "canonical_sha256": canonical_sha256,
                    "struct_features": recomputed_features,
                    "trace_equal": trace[0] if isinstance(trace, (tuple, list)) else None,
                    "trace_note": (
                        trace[1]
                        if isinstance(trace, (tuple, list)) and len(trace) > 1
                        else None
                    ),
                }
            )
            if recomputed_hash != record["logged_canon_hash"]:
                raise ValueError("recomputed canonical hash differs from reward-time log")
            if recomputed_features != record["logged_struct_features"]:
                raise ValueError("recomputed structural features differ from reward-time log")
            if not isinstance(trace, (tuple, list)) or len(trace) != 2 or trace[0] is not True:
                raise ValueError(f"compile/trace equivalence did not pass exactly: {trace!r}")
            result["accepted"] = True
            result["ok"] = True
            result["rejected"] = False
            canonical_groups[canonical_sha256].append(filename)
        except Exception as exc:  # Preserve all gate failures as structured evidence.
            result["failure"] = _jsonable_failure(exc)
            result["ok"] = False
            result["rejected"] = isinstance(exc, Unsupported)
            failure_counts[type(exc).__name__] += 1
            failure_details.append({"file": filename, **_jsonable_failure(exc)})
        per_file_by_name[filename] = {"file": filename, **result}

    collision_details: list[dict[str, Any]] = []
    for canonical_digest, files in sorted(canonical_groups.items()):
        designs = sorted({per_file_by_name[name]["design"] for name in files})
        if len(designs) > 1:
            collision_details.append(
                {
                    "canonical_sha256": canonical_digest,
                    "files": sorted(files),
                    "designs": designs,
                }
            )

    per_file = [per_file_by_name[name] for name in sorted(per_file_by_name)]
    passed = sum(1 for item in per_file if item["accepted"])
    contract = {
        "schema_version": 1,
        "study_id": study["study_id"],
        "manifest": {
            "path": manifest_path.as_posix(),
            "sha256": sha256_file(manifest_path),
        },
        "backend": "canonicalize.py plus Icarus compile/trace equivalence",
        "n": len(eligible_records),
        "passed": passed,
        "rejected": len(eligible_records) - passed,
        "failures": dict(sorted(failure_counts.items())),
        "failure_details": failure_details,
        "collisions": len(collision_details),
        "collision_details": collision_details,
        "pre_contract_errors": errors,
        "per_file": per_file,
    }
    contract_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--prereg", type=Path, default=Path("preregistration_study2.json"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("rtl/sealed_rf_reward_eligible_study2")
    )
    parser.add_argument(
        "--manifest", type=Path, default=Path("rf_reward_eligible_manifest_study2.json")
    )
    parser.add_argument(
        "--contract", type=Path, default=Path("rf_reward_eligible_contract_study2.json")
    )
    args = parser.parse_args()
    try:
        contract = audit(args.logs, args.prereg, args.output_dir, args.manifest, args.contract)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    ok = (
        not contract["pre_contract_errors"]
        and contract["rejected"] == 0
        and not any(contract["failures"].values())
        and contract["collisions"] == 0
    )
    print(
        f"Study 2 RF gate: {contract['passed']}/{contract['n']} passed; "
        f"rejected={contract['rejected']}; collisions={contract['collisions']}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
