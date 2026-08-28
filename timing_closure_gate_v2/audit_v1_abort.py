#!/usr/bin/env python3
"""Freeze a read-only, fully hashed audit of the irreversibly failed v1 run."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from common import HERE, ROOT, V1, V1_MANIFEST_SHA256, canonical_json_bytes, load_json, sha256_bytes, sha256_file, verify_v1_manifest, write_json_atomic


REPORT = HERE / "v1_failure_abort_report.json"
DIGEST = HERE / "v1_failure_abort_report.sha256"
INTERNAL_READ_RE = re.compile(
    r'''couldn't read file\s+"(?P<path>[A-Za-z]:[/\\]Xilinx[/\\]Vivado[/\\]2023\.1[/\\]scripts[/\\]rt[/\\]data[/\\][^"]+\.tcl)"\s*:\s*(?P<reason>No error|no such file or directory|permission denied|invalid argument|I/O error)''',
    re.I,
)


def active_v1_processes() -> list[dict]:
    if os.name != "nt":
        return []
    command = (
        "$self=$PID; Get-CimInstance Win32_Process | "
        "Where-Object {$_.ProcessId -ne $self -and $_.Name -match 'python|vivado|cmd' -and "
        "$_.CommandLine -like '*timing_closure_gate_v1*'} | "
        "Select-Object ProcessId,ParentProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    proc = subprocess.run(["powershell", "-NoProfile", "-Command", command], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"could not verify v1 quiescence: {proc.stderr.strip()}")
    text = proc.stdout.strip()
    if not text:
        return []
    value = json.loads(text)
    return value if isinstance(value, list) else [value]


def inventory_v1() -> list[dict]:
    rows = []
    for path in sorted((p for p in V1.rglob("*") if p.is_file()), key=lambda p: p.relative_to(V1).as_posix()):
        stat = path.stat()
        rows.append({
            "path": path.relative_to(V1).as_posix(),
            "bytes": stat.st_size,
            "sha256": sha256_file(path),
            "mtime_utc": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        })
    return rows


def read_ledger(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        row["ledger_line"] = line_number
        rows.append(row)
    return rows


def classify_trial(row: dict, trial_dir: Path) -> tuple[str, dict | None]:
    log_text = ""
    for name in ("vivado.stdout.log", "vivado.stderr.log"):
        path = trial_dir / name
        if path.is_file():
            log_text += path.read_text(encoding="utf-8", errors="replace")
    match = INTERNAL_READ_RE.search(log_text)
    if match and not row.get("valid_measurement"):
        return "INFRASTRUCTURE_INTERNAL_TCL_READ", {
            "path": match.group("path").replace("\\", "/"),
            "reason": match.group("reason"),
        }
    if row.get("valid_measurement"):
        return "VALID_MEASUREMENT", None
    if not (trial_dir / "vivado_result.json").is_file() or int(row.get("returncode", 0)) == 4294967295:
        return "INTERRUPTED_PROCESS", None
    return "INVALID_NON_ALLOWLISTED", None


def parse_status() -> dict:
    status_path = V1 / "pilot_launcher.status"
    result = {}
    for line in status_path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def build_report() -> dict:
    active = active_v1_processes()
    if active:
        raise RuntimeError(f"v1 is still active: {active}")
    manifest, digest = verify_v1_manifest()
    inventory_first = inventory_v1()
    inventory_second = inventory_v1()
    stable_first = [(row["path"], row["bytes"], row["sha256"]) for row in inventory_first]
    stable_second = [(row["path"], row["bytes"], row["sha256"]) for row in inventory_second]
    if stable_first != stable_second:
        raise RuntimeError("v1 changed during the audit")
    inventory_digest = sha256_bytes(canonical_json_bytes(stable_first))
    launcher_status = parse_status()
    stopped = dt.datetime.fromisoformat(launcher_status["stopped_utc"].replace("Z", "+00:00"))
    candidates = []
    infra_events = []
    interrupted_events = []
    post_status_paths = []
    for row in inventory_first:
        timestamp = dt.datetime.fromisoformat(row["mtime_utc"].replace("Z", "+00:00"))
        if timestamp > stopped:
            post_status_paths.append(row["path"])
    for candidate in manifest["candidates"]:
        candidate_dir = V1 / "results" / candidate["candidate_id"]
        ledger_path = candidate_dir / "trials.jsonl"
        ledger = read_ledger(ledger_path)
        trial_rows = []
        ledger_dirs = set()
        for row in ledger:
            trial_dir = ROOT / row["trial_dir"]
            ledger_dirs.add(trial_dir.name)
            classification, detail = classify_trial(row, trial_dir)
            trial_summary = {
                "ledger_line": row["ledger_line"],
                "trial_dir": row["trial_dir"],
                "period_ns": row.get("period_ns"),
                "purpose": row.get("purpose"),
                "attempt": row.get("attempt"),
                "valid_measurement": row.get("valid_measurement"),
                "closed": row.get("closed"),
                "returncode": row.get("returncode"),
                "classification": classification,
                "detail": detail,
            }
            trial_rows.append(trial_summary)
            if classification == "INFRASTRUCTURE_INTERNAL_TCL_READ":
                infra_events.append({"candidate_id": candidate["candidate_id"], **trial_summary})
            if classification == "INTERRUPTED_PROCESS":
                interrupted_events.append({"candidate_id": candidate["candidate_id"], **trial_summary})
        orphan_dirs = []
        if candidate_dir.is_dir():
            for trial_dir in sorted(candidate_dir.glob("trial_*")):
                if trial_dir.name not in ledger_dirs:
                    orphan = {
                        "candidate_id": candidate["candidate_id"],
                        "trial_dir": trial_dir.relative_to(ROOT).as_posix(),
                        "classification": "INTERRUPTED_UNLEDGERED_DIRECTORY",
                        "file_count": sum(path.is_file() for path in trial_dir.rglob("*")),
                    }
                    orphan_dirs.append(orphan)
                    interrupted_events.append(orphan)
        closure_path = candidate_dir / "closure_result.json"
        closure = load_json(closure_path) if closure_path.is_file() else None
        candidates.append({
            "candidate_id": candidate["candidate_id"],
            "candidate_order": len(candidates) + 1,
            "result_directory_exists": candidate_dir.is_dir(),
            "ledger_rows": len(ledger),
            "trial_directories": len(list(candidate_dir.glob("trial_*"))) if candidate_dir.is_dir() else 0,
            "closure_result_status": closure.get("status") if closure else None,
            "closure_failure_reason": closure.get("failure_reason") if closure else None,
            "closure_result_sha256": sha256_file(closure_path) if closure else None,
            "trials": trial_rows,
            "unledgered_trial_directories": orphan_dirs,
        })
    failed = next((row for row in candidates if row["candidate_id"] == "c02_fir_rf_fir42_v6_8b"), None)
    if not failed or failed["closure_result_status"] != "FAILED":
        raise RuntimeError("the irreversible c02 v1 failure is absent")
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v1",
        "report_type": "failure_abort_attestation",
        "v1_protocol_status": "IRREVERSIBLE_FAIL_AND_ABORTED",
        "scientific_endpoint_status": "NOT_EVALUABLE",
        "gate_pass_possible": False,
        "manifest_sha256": digest,
        "launcher_status": launcher_status,
        "quiescence": {"active_v1_process_count": 0, "two_identical_inventory_passes": True},
        "operator_intervention": {
            "recorded_launcher_pid": 60308,
            "orphan_writer_detected_after_recorded_stop": True,
            "final_exact_stopped_processes": [42228, 37680, 47008],
            "note": "The runner survived the recorded launcher stop, completed c03, and entered c04. The exact orphan v1 runner/cmd/Vivado tree was then stopped; all partial files were retained."
        },
        "irreversible_failure": {
            "candidate_id": "c02_fir_rf_fir42_v6_8b",
            "v1_failure_reason": failed["closure_failure_reason"],
            "closure_result_sha256": failed["closure_result_sha256"],
            "causal_classification": "INFRASTRUCTURE_INTERNAL_TCL_READ_FAILURE",
            "scientific_interpretation": "The v1 implementation encoded this as a permanent zero-scored failure, making the v1 gate irreversibly fail. The diagnostic evidence does not support treating it as candidate performance."
        },
        "summary": {
            "expected_candidates": 10,
            "candidate_directories": sum(row["result_directory_exists"] for row in candidates),
            "complete_results": sum(row["closure_result_status"] == "COMPLETE" for row in candidates),
            "failed_results": sum(row["closure_result_status"] == "FAILED" for row in candidates),
            "missing_results": sum(row["closure_result_status"] is None for row in candidates),
            "ledger_rows": sum(row["ledger_rows"] for row in candidates),
            "infrastructure_internal_tcl_read_events": len(infra_events),
            "interrupted_events": len(interrupted_events),
            "post_recorded_stop_file_count": len(post_status_paths),
        },
        "infrastructure_events": infra_events,
        "interrupted_events": interrupted_events,
        "post_recorded_stop_paths": post_status_paths,
        "candidates": candidates,
        "diagnosis": {
            "most_likely_class": "transient host/tool-installation file-read instability in Vivado helper processes",
            "confidence": "moderate",
            "evidence": [
                "Four failures named four different existing Tcl files under the same pinned Vivado installation directory.",
                "The failures occurred during Vivado synthesis initialization, before candidate-dependent timing outcomes existed.",
                "Retries at identical candidate and period succeeded for c03 and c04; c02 failed on two different files.",
                "The files exist and repeated independent raw SHA-256 reads were stable after abort.",
                "The C: NTFS volume and physical SSD reported Healthy/OK and no matching disk, NTFS, or Defender event was present in the failure window."
            ],
            "not_established": "The retained evidence cannot distinguish a Vivado 2023.1 helper-process defect from a transient Windows filesystem/minifilter interaction such as real-time security scanning. Candidate RTL, requested period, and deterministic file absence are not plausible common causes."
        },
        "artifact_inventory": {
            "file_count": len(inventory_first),
            "total_bytes": sum(row["bytes"] for row in inventory_first),
            "inventory_sha256": inventory_digest,
            "files": inventory_first,
        },
    }


def check_report() -> str:
    if not REPORT.is_file() or not DIGEST.is_file():
        raise RuntimeError("frozen v1 abort report is missing")
    report = load_json(REPORT)
    digest = sha256_file(REPORT)
    if DIGEST.read_text(encoding="ascii").strip().lower() != digest:
        raise RuntimeError("v1 abort report digest mismatch")
    active = active_v1_processes()
    if active:
        raise RuntimeError(f"v1 became active after freeze: {active}")
    current = inventory_v1()
    expected = [(row["path"], row["bytes"], row["sha256"]) for row in report["artifact_inventory"]["files"]]
    actual = [(row["path"], row["bytes"], row["sha256"]) for row in current]
    if actual != expected:
        raise RuntimeError("v1 artifacts changed after abort report freeze")
    return digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("choose exactly one of --write or --check")
    try:
        if args.write:
            if REPORT.exists() or DIGEST.exists():
                raise RuntimeError("refusing to overwrite frozen v1 abort report")
            report = build_report()
            write_json_atomic(REPORT, report)
            digest = sha256_file(REPORT)
            DIGEST.write_text(digest + "\n", encoding="ascii")
        else:
            digest = check_report()
        print(f"PASS v1_failure_abort_report_sha256={digest}")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
