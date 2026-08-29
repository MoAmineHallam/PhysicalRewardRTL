#!/usr/bin/env python3
"""Statically audit every task in the pinned RTLLM 2.0 snapshot."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from common import (
    CATEGORIES,
    MODULE_RE,
    discover_tasks,
    expected_module,
    load_json,
    sensitivity_audit,
    sha256_file,
    strip_verilog_comments,
    task_id,
    verify_upstream_identity,
    write_json,
)


def audit_task(root: Path, task_dir: Path) -> dict:
    identifier = task_id(root, task_dir)
    category = task_dir.relative_to(root).parts[0]
    description_path = task_dir / "design_description.txt"
    testbench_path = task_dir / "testbench.v"
    references = sorted(task_dir.glob("verified*.v"))
    description = description_path.read_text(encoding="utf-8", errors="replace")
    testbench = testbench_path.read_text(encoding="utf-8", errors="replace") if testbench_path.exists() else ""
    reference = references[0].read_text(encoding="utf-8", errors="replace") if len(references) == 1 else ""
    expected = expected_module(description)
    modules = MODULE_RE.findall(reference)
    tb_modules = MODULE_RE.findall(testbench)
    sens = sensitivity_audit(reference)
    clean_ref = strip_verilog_comments(reference)
    clean_tb = strip_verilog_comments(testbench)

    tb_pass_markers = re.findall(r'(?is)\$display\s*\(\s*"([^"\r\n]*pass[^"\r\n]*)"', testbench)
    tb_failure_markers = re.findall(
        r'(?is)\$display\s*\(\s*"([^"\r\n]*(?:fail|error|mismatch)[^"\r\n]*)"', testbench
    )
    instantiates_expected = bool(
        expected
        and re.search(
            rf"(?is)\b{re.escape(expected)}\b\s*(?:#\s*\(.*?\)\s*)?[A-Za-z_]\w*\s*\(",
            clean_tb,
        )
    )
    external_calls = sorted(
        set(re.findall(r"(?i)\$(readmem[hb]|fopen|fscanf|fread)", clean_tb)), key=str.lower
    )
    reference_system_tasks = sorted(set(re.findall(r"\$[A-Za-z_]\w*", clean_ref)), key=str.lower)
    reference_initial = bool(re.search(r"(?m)^\s*initial\b", clean_ref))
    reference_delay = bool(re.search(r"#\s*(?!\()(?:(?:\d)|(?:[A-Za-z_]\w*))", clean_ref))
    reference_real = bool(re.search(r"(?i)\b(?:real|shortreal|realtime)\b", clean_ref))
    vendor_primitives = sorted(
        set(re.findall(r"(?i)\b(?:BUFG\w*|MMCME\w*|PLLE\w*|RAMB\w*|DSP48\w*|xpm_\w+)\b", clean_ref))
    )
    tb_random = sorted(set(re.findall(r"(?i)\$(?:u?random)\b", clean_tb)))
    tb_break = bool(re.search(r"(?m)^\s*break\s*;", clean_tb))
    tb_finish = bool(re.search(r"\$finish\b", clean_tb))

    reasons: list[str] = []
    if len(references) != 1:
        reasons.append("reference_file_count_not_one")
    if not expected:
        reasons.append("missing_specified_module_name")
    if not testbench_path.exists():
        reasons.append("missing_testbench")
    if not sens["edge_signals"]:
        reasons.append("reference_not_edge_clocked")
    if len(sens["clock_signals"]) != 1:
        reasons.append("reference_not_single_clock")
    if sens["mixed_edge_level_sensitivities"]:
        reasons.append("reference_mixed_edge_level_sensitivity")
    if reference_initial:
        reasons.append("reference_has_initial")
    if reference_delay:
        reasons.append("reference_has_delay_control")
    if reference_real:
        reasons.append("reference_has_real_type")
    if reference_system_tasks:
        reasons.append("reference_has_system_task")
    if vendor_primitives:
        reasons.append("reference_has_vendor_primitive")
    if not tb_finish:
        reasons.append("testbench_missing_finish")
    if not tb_pass_markers or not tb_failure_markers:
        reasons.append("testbench_not_self_checking")
    if external_calls:
        reasons.append("testbench_external_file_dependency")
    if tb_break:
        reasons.append("testbench_break_statement")
    if not instantiates_expected:
        reasons.append("testbench_missing_specified_dut_instantiation")

    return {
        "task_id": identifier,
        "category": category,
        "expected_module": expected,
        "task_directory": identifier,
        "description": {
            "path": f"{identifier}/design_description.txt",
            "sha256": sha256_file(description_path),
            "bytes": description_path.stat().st_size,
        },
        "testbench": {
            "path": f"{identifier}/testbench.v",
            "sha256": sha256_file(testbench_path) if testbench_path.exists() else None,
            "bytes": testbench_path.stat().st_size if testbench_path.exists() else None,
            "top_modules": tb_modules,
            "pass_markers": tb_pass_markers,
            "failure_markers": tb_failure_markers,
            "has_finish": tb_finish,
            "random_calls": tb_random,
            "external_calls": external_calls,
            "has_break": tb_break,
            "instantiates_expected_module": instantiates_expected,
        },
        "reference": {
            "path": f"{identifier}/{references[0].name}" if len(references) == 1 else None,
            "sha256": sha256_file(references[0]) if len(references) == 1 else None,
            "bytes": references[0].stat().st_size if len(references) == 1 else None,
            "modules": modules,
            "top_module": modules[0] if modules else None,
            "clock_signals": sens["clock_signals"],
            "reset_signals": sens["reset_signals"],
            "edge_signals": sens["edge_signals"],
            "mixed_edge_level_sensitivities": sens["mixed_edge_level_sensitivities"],
            "has_initial": reference_initial,
            "has_delay_control": reference_delay,
            "has_real_type": reference_real,
            "system_tasks": reference_system_tasks,
            "vendor_primitives": vendor_primitives,
        },
        "static_eligible": not reasons,
        "static_exclusion_reasons": reasons,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    package_root = args.package_root.resolve()
    pin = load_json(package_root / "upstream_pin.json")
    upstream = args.upstream.resolve()
    identity = verify_upstream_identity(upstream, pin)
    tasks = [audit_task(upstream, p) for p in discover_tasks(upstream)]
    counts = Counter(t["category"] for t in tasks)
    if len(tasks) != 50 or set(counts) != set(CATEGORIES):
        raise SystemExit(f"FAIL: expected 50 tasks across {CATEGORIES}, got {len(tasks)} and {dict(counts)}")
    report = {
        "schema_version": 1,
        "status": "PASS",
        "upstream": identity,
        "task_count": len(tasks),
        "category_counts": dict(sorted(counts.items())),
        "static_eligible_count": sum(t["static_eligible"] for t in tasks),
        "tasks": tasks,
    }
    output = args.output or package_root / "audit_manifest.json"
    write_json(output, report)
    print(f"PASS audit task_count={len(tasks)} static_eligible={report['static_eligible_count']} output={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
