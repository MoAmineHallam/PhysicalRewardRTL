#!/usr/bin/env python3
"""Run only official-reference/oracle self-tests for statically eligible tasks."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from common import MODULE_RE, load_json, sha256_bytes, verify_upstream_identity, write_json


def tool_version(command: str) -> str:
    proc = subprocess.run([command, "-V"], text=True, capture_output=True, check=False)
    line = (proc.stdout + proc.stderr).splitlines()
    return line[0].strip() if line else "unknown"


def run_one(upstream: Path, task: dict, iverilog: str, vvp: str, timeout_seconds: int) -> dict:
    task_dir = upstream / task["task_directory"]
    reference_path = upstream / task["reference"]["path"]
    reference = reference_path.read_text(encoding="utf-8", errors="replace")
    expected = task["expected_module"]
    reference_top = task["reference"]["top_module"]
    if not reference_top:
        return {"task_id": task["task_id"], "status": "FAIL", "reason": "missing_reference_top"}
    renamed, replacements = re.subn(
        rf"(?m)^(\s*module\s+){re.escape(reference_top)}\b",
        rf"\g<1>{expected}",
        reference,
        count=1,
    )
    if replacements != 1:
        return {"task_id": task["task_id"], "status": "FAIL", "reason": "reference_rename_failed"}
    testbench = (task_dir / "testbench.v").read_text(encoding="utf-8", errors="replace")
    tb_modules = MODULE_RE.findall(testbench)
    if not tb_modules:
        return {"task_id": task["task_id"], "status": "FAIL", "reason": "missing_testbench_top"}
    tb_top = tb_modules[0]
    with tempfile.TemporaryDirectory(prefix="rtllm_ref_") as tmp_name:
        tmp = Path(tmp_name)
        (tmp / "reference_under_test.v").write_text(renamed, encoding="utf-8", newline="\n")
        (tmp / "testbench.v").write_text(testbench, encoding="utf-8", newline="\n")
        output = tmp / "simv"
        compile_proc = subprocess.run(
            [iverilog, "-g2012", "-s", tb_top, "-o", str(output), "reference_under_test.v", "testbench.v"],
            cwd=tmp,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
        compile_text = (compile_proc.stdout + compile_proc.stderr).replace(str(tmp), "<TMP>")
        if compile_proc.returncode != 0:
            return {
                "task_id": task["task_id"],
                "status": "FAIL",
                "reason": "compile_failed",
                "compile_returncode": compile_proc.returncode,
                "compile_log": compile_text,
                "compile_log_sha256": sha256_bytes(compile_text.encode("utf-8")),
            }
        run_records = []
        for _ in range(2):
            try:
                run_proc = subprocess.run(
                    [vvp, str(output)],
                    cwd=tmp,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                partial = ((exc.stdout or "") + (exc.stderr or "")).replace(str(tmp), "<TMP>")
                return {
                    "task_id": task["task_id"],
                    "status": "FAIL",
                    "reason": "simulation_timeout",
                    "run_log": partial,
                    "run_log_sha256": sha256_bytes(partial.encode("utf-8")),
                }
            run_text = (run_proc.stdout + run_proc.stderr).replace(str(tmp), "<TMP>")
            run_records.append({"returncode": run_proc.returncode, "text": run_text})
        run_text = run_records[0]["text"]
        replay_identical = run_records[0] == run_records[1]
        pass_marker = any(marker.lower() in run_text.lower() for marker in task["testbench"]["pass_markers"])
        status = "PASS" if run_records[0]["returncode"] == 0 and pass_marker and replay_identical else "FAIL"
        if not replay_identical:
            reason = "non_deterministic_replay"
        elif run_records[0]["returncode"] != 0 or not pass_marker:
            reason = "official_pass_marker_absent_or_nonzero_exit"
        else:
            reason = None
        return {
            "task_id": task["task_id"],
            "status": status,
            "reason": reason,
            "expected_module": expected,
            "reference_top_before_rename": reference_top,
            "testbench_top": tb_top,
            "compile_returncode": compile_proc.returncode,
            "run_returncode": run_records[0]["returncode"],
            "compile_log": compile_text,
            "compile_log_sha256": sha256_bytes(compile_text.encode("utf-8")),
            "run_log": run_text,
            "run_log_sha256": sha256_bytes(run_text.encode("utf-8")),
            "official_pass_marker_seen": pass_marker,
            "replay_count": 2,
            "replay_identical": replay_identical,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--iverilog", default="iverilog")
    parser.add_argument("--vvp", default="vvp")
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()
    package_root = args.package_root.resolve()
    pin = load_json(package_root / "upstream_pin.json")
    identity = verify_upstream_identity(args.upstream.resolve(), pin)
    audit = load_json(args.audit or package_root / "audit_manifest.json")
    if audit.get("status") != "PASS" or audit.get("task_count") != 50:
        raise SystemExit("FAIL: static audit is absent or invalid")
    if shutil.which(args.iverilog) is None or shutil.which(args.vvp) is None:
        raise SystemExit("FAIL: iverilog and vvp are required for the reference preflight")
    eligible = [task for task in audit["tasks"] if task["static_eligible"]]
    results = [
        run_one(args.upstream.resolve(), task, args.iverilog, args.vvp, args.timeout_seconds)
        for task in eligible
    ]
    report = {
        "schema_version": 1,
        "status": "PASS",
        "scope": "official reference plus official testbench only; no generated RTL and no Vivado",
        "upstream": identity,
        "tools": {
            "iverilog": tool_version(args.iverilog),
            "vvp_command": Path(args.vvp).name,
            "language_flag": "-g2012",
            "timeout_seconds_per_task": args.timeout_seconds,
        },
        "attempted_count": len(results),
        "passed_count": sum(result["status"] == "PASS" for result in results),
        "failed_count": sum(result["status"] != "PASS" for result in results),
        "results": results,
    }
    output = args.output or package_root / "reference_preflight.json"
    write_json(output, report)
    print(
        f"PASS reference preflight attempted={report['attempted_count']} "
        f"passed={report['passed_count']} failed={report['failed_count']} output={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
