#!/usr/bin/env python3
"""Run the prospective V5 post-restart Vivado stability gate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from timing_closure_gate_v4.run_stability_gate import (
    PROBE, TCL, run_one,
)
from timing_closure_gate_v4.stability_common import (
    ROOT, VIVADO_ROOT, raw_dependency_snapshot, read_json, sha256_file,
    write_json_new,
)


HERE = Path(__file__).resolve().parent
BASELINE = HERE / "dependency_baseline.json"
DEFAULT_CAMPAIGN = HERE / "stability_campaign_001"
DEFAULT_SCRATCH_ROOT = Path(r"C:\VGT5S001")
RUNS = 40


def build_attestation(baseline: dict, rows: list[dict],
                      scratch_root: Path) -> dict:
    all_ok = len(rows) == RUNS and all(
        row["valid_measurement"] for row in rows)
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v5",
        "scope": "post-restart pre-candidate synthetic infrastructure stability gate",
        "contains_study2_rtl": False,
        "scratch_root": str(scratch_root),
        "explicit_tempdir": True,
        "reused_v4_closure_tcl_path": TCL.relative_to(ROOT).as_posix(),
        "reused_v4_closure_tcl_sha256_raw": sha256_file(TCL),
        "reused_v4_probe_path": PROBE.relative_to(ROOT).as_posix(),
        "reused_v4_probe_sha256_raw": sha256_file(PROBE),
        "baseline_sha256_raw": sha256_file(BASELINE),
        "baseline_dependency_aggregate_sha256_raw":
            baseline["aggregate_sha256_raw"],
        "required_first_attempts": RUNS,
        "retry_within_campaign": 0,
        "runs": rows,
        "verdict": "PASS" if all_ok else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivado", default=str(
        VIVADO_ROOT / "bin" / "vivado.bat"))
    parser.add_argument("--baseline", default=str(BASELINE))
    parser.add_argument("--campaign", default=str(DEFAULT_CAMPAIGN))
    parser.add_argument("--scratch-root", default=str(DEFAULT_SCRATCH_ROOT))
    args = parser.parse_args()
    campaign = Path(args.campaign)
    scratch_root = Path(args.scratch_root)
    attestation_path = campaign / "stability_attestation.json"
    try:
        if campaign.exists():
            raise RuntimeError(f"campaign directory must be new: {campaign}")
        if scratch_root.exists():
            raise RuntimeError(f"scratch root must be new: {scratch_root}")
        baseline = read_json(Path(args.baseline))
        current = raw_dependency_snapshot(VIVADO_ROOT)
        expected = dict(current)
        expected.update({
            "study_id": "timing_closure_gate_v5",
            "scope": "Vivado 2023.1 full scripts/rt raw dependency baseline before post-restart V5 stability gate",
            "pinned_tcl_count": sum(
                item["path"].endswith(".tcl") for item in current["files"]),
            "raw_read_repetitions": 20,
        })
        if baseline != expected:
            raise RuntimeError("dependency baseline is absent or no longer current")
        campaign.mkdir(parents=True)
        rows = []
        for index in range(1, RUNS + 1):
            row = run_one(index, Path(args.vivado), baseline, campaign,
                          scratch_root)
            rows.append(row)
            if not row["valid_measurement"]:
                break
        attestation = build_attestation(baseline, rows, scratch_root)
        write_json_new(attestation_path, attestation)
        print(f"STABILITY {attestation['verdict']}")
        print("attestation_sha256_raw=" + sha256_file(attestation_path))
        return 0 if attestation["verdict"] == "PASS" else 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
