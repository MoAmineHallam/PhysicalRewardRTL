#!/usr/bin/env python3
"""Validate V7 candidate records and publish the frozen pilot verdict."""

from __future__ import annotations

import argparse
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from timing_closure_gate_v1.validate_gate import sign, smape, spearman  # noqa: E402

try:
    from .common import (
        V7_ATTESTATION_SHA, atomic_json, canonical_json_bytes, read_json,
        sha256_file, verify_inputs, verify_package,
    )
except ImportError:
    from common import (
        V7_ATTESTATION_SHA, atomic_json, canonical_json_bytes, read_json,
        sha256_file, verify_inputs, verify_package,
    )


DEFAULT_RESULTS = HERE / "results"
STUDY_ID = "timing_closure_candidate_v7"


def validate_trial(row: dict, candidate: dict, v1_digest: str,
                   package_digest: str) -> list[str]:
    errors = []
    expected = {
        "schema_version": 1,
        "study_id": STUDY_ID,
        "v1_manifest_sha256": v1_digest,
        "candidate_package_sha256": package_digest,
        "v7_stability_attestation_sha256": V7_ATTESTATION_SHA,
        "vivado_version": "2026.1",
        "candidate_id": candidate["candidate_id"],
    }
    for key, value in expected.items():
        if row.get(key) != value:
            errors.append(f"trial_{key}_mismatch")
    try:
        trial_dir = ROOT / row["trial_dir"]
        record = trial_dir / "trial_record.json"
        if not record.is_file() or record.read_bytes() != canonical_json_bytes(row):
            errors.append("trial_record_mismatch")
        for key, name in (("stdout_sha256_raw", "vivado.stdout.log"),
                          ("stderr_sha256_raw", "vivado.stderr.log"),
                          ("result_sha256_raw", "vivado_result.json")):
            expected_hash = row.get(key)
            path = trial_dir / name
            if expected_hash is not None and (
                    not path.is_file() or sha256_file(path) != expected_hash):
                errors.append(f"{key}_mismatch")
    except (KeyError, OSError, ValueError):
        errors.append("trial_artifact_path_invalid")
    if row.get("valid_measurement"):
        if (row.get("returncode") != 0
                or row.get("before_dependency_guard", {}).get("ok") is not True
                or row.get("after_dependency_guard", {}).get("ok") is not True):
            errors.append("valid_trial_guard_or_returncode_failed")
        vivado = row.get("vivado", {})
        required = (
            int(vivado.get("compiled", 0)) == 1,
            int(vivado.get("implemented", 0)) == 1,
            int(vivado.get("clock_count", 0)) == 1,
            int(vivado.get("setup_path_count", 0)) > 0,
            int(vivado.get("summary_parse_ok", 0)) == 1,
            int(vivado.get("unconstrained_path_count", -1)) == 0,
            int(vivado.get("route_clean", 0)) == 1,
            int(vivado.get("constraint_coverage_ok", 0)) == 1,
        )
        if not all(required):
            errors.append("valid_trial_measurement_fields_failed")
        if not math.isclose(float(vivado.get("period_ns", math.nan)),
                            float(row.get("period_ns", math.nan)),
                            rel_tol=0.0, abs_tol=1e-9):
            errors.append("trial_period_mismatch")
        if row.get("closed") is not bool(int(vivado.get("closed", 0)) == 1):
            errors.append("trial_closed_mismatch")
    return errors


def load_result(candidate: dict, v1_digest: str, package_digest: str,
                results: Path) -> tuple[dict | None, Path, list[str]]:
    path = results / candidate["candidate_id"] / "closure_result.json"
    if not path.is_file():
        return None, path, ["result_missing"]
    try:
        result = read_json(path)
    except Exception as exc:
        return None, path, [f"invalid_result_json:{exc}"]
    errors = []
    expected = {
        "schema_version": 1,
        "study_id": STUDY_ID,
        "scope": "pilot_10",
        "v1_manifest_sha256": v1_digest,
        "candidate_package_sha256": package_digest,
        "v7_stability_attestation_sha256": V7_ATTESTATION_SHA,
        "vivado_version": "2026.1",
        "candidate_id": candidate["candidate_id"],
        "family": candidate["family"],
        "design": candidate["design"],
        "arm": candidate["arm"],
        "module": candidate["module"],
    }
    for key, value in expected.items():
        if result.get(key) != value:
            errors.append(f"{key}_mismatch")
    if not math.isclose(float(result.get("old_fmax_mhz", math.nan)),
                        float(candidate["old_fmax_mhz"]),
                        rel_tol=1e-12, abs_tol=1e-12):
        errors.append("old_fmax_mismatch")
    trials = result.get("trials", [])
    if not isinstance(trials, list) or result.get("trial_count") != len(trials):
        errors.append("trial_count_mismatch")
        trials = []
    for row in trials:
        errors.extend(validate_trial(row, candidate, v1_digest, package_digest))
    if result.get("status") == "COMPLETE":
        closure = float(result.get("closure_fmax_mhz", math.nan))
        tight = float(result.get("tight_failing_period_ns", math.nan))
        loose = float(result.get("loose_passing_period_ns", math.nan))
        width = float(result.get("relative_bracket_width", math.inf))
        if not (math.isfinite(closure) and closure > 0.0
                and math.isfinite(tight) and math.isfinite(loose)
                and 1.0 <= tight < loose <= 200.0
                and width <= 0.01 + 1e-12
                and math.isclose(closure, 1000.0 / loose,
                                 rel_tol=1e-12, abs_tol=1e-12)):
            errors.append("invalid_closure_result")
        purposes = [row.get("purpose") for row in trials
                    if row.get("valid_measurement")]
        if "confirm_fail" not in purposes or "confirm_pass" not in purposes:
            errors.append("boundary_confirmation_missing")
    elif result.get("status") == "FAILED":
        if result.get("closure_fmax_mhz") != 0.0:
            errors.append("failed_candidate_not_zero_scored")
        if not result.get("failure_reason"):
            errors.append("failure_reason_missing")
    else:
        errors.append("unknown_status")
    return result, path, errors


def build_gate(manifest: dict, v1_digest: str, package_digest: str,
               results: Path) -> tuple[dict | None, list[dict]]:
    loaded = []
    failures = []
    generated_from = [
        {"path": "timing_closure_gate_v1/manifest.json",
         "sha256_raw": v1_digest},
        {"path": "timing_closure_gate_v7/stability_campaign_001/stability_attestation.json",
         "sha256_raw": V7_ATTESTATION_SHA},
        {"path": "timing_closure_candidate_v7/manifest.json",
         "sha256_raw": package_digest},
    ]
    for candidate in manifest["candidates"]:
        result, path, errors = load_result(
            candidate, v1_digest, package_digest, results)
        if result is None:
            failures.append({"candidate_id": candidate["candidate_id"],
                             "errors": errors})
            continue
        loaded.append((candidate, result))
        generated_from.append({
            "path": path.resolve().relative_to(ROOT).as_posix(),
            "sha256_raw": sha256_file(path),
        })
        if errors:
            failures.append({"candidate_id": candidate["candidate_id"],
                             "errors": sorted(set(errors))})
    if len(loaded) != 10:
        return None, failures

    complete = (not failures and all(
        result.get("status") == "COMPLETE" for _, result in loaded))
    old = [float(candidate["old_fmax_mhz"]) for candidate, _ in loaded]
    closure = [float(result["closure_fmax_mhz"]) for _, result in loaded]
    rho = spearman(old, closure)
    candidate_smape = [smape(a, b) for a, b in zip(old, closure)]
    median_error = statistics.median(candidate_smape)
    by_design: dict[str, dict] = {}
    for candidate, result in loaded:
        by_design.setdefault(candidate["design"], {})[candidate["arm"]] = (
            candidate, result)
    pairs, differences = [], []
    reversals = 0
    non_tied = 0
    for design in sorted(by_design):
        pair = by_design[design]
        if set(pair) != {"sft", "rf"}:
            failures.append({"design": design, "errors": ["incomplete_pair"]})
            continue
        sft_c, sft_r = pair["sft"]
        rf_c, rf_r = pair["rf"]
        old_diff = float(rf_c["old_fmax_mhz"]) - float(sft_c["old_fmax_mhz"])
        closure_diff = (float(rf_r["closure_fmax_mhz"])
                        - float(sft_r["closure_fmax_mhz"]))
        differences.append(closure_diff)
        scale = 0.5 * (abs(float(rf_c["old_fmax_mhz"]))
                       + abs(float(sft_c["old_fmax_mhz"])))
        old_sign = sign(old_diff, tolerance=0.01 * scale)
        closure_sign = sign(closure_diff)
        reversal = old_sign != 0 and closure_sign != old_sign
        non_tied += int(old_sign != 0)
        reversals += int(reversal)
        pairs.append({"design": design,
                      "old_rf_minus_sft_mhz": old_diff,
                      "closure_rf_minus_sft_mhz": closure_diff,
                      "old_proxy_tie": old_sign == 0,
                      "sign_reversal": reversal})
    paired_mean = statistics.fmean(differences) if differences else None
    criteria = {
        "complete_and_constrained": bool(complete and len(pairs) == 5),
        "spearman_ge_0_90": bool(rho is not None and rho >= 0.90),
        "median_smape_le_0_15": bool(median_error <= 0.15),
        "paired_direction": bool(
            paired_mean is not None and paired_mean > 0.0 and reversals <= 1),
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    if verdict == "FAIL" and not failures:
        failures.append({
            "gate": "threshold_failure",
            "failed_criteria": [key for key, ok in criteria.items() if not ok],
        })
    return {
        "schema_version": 1,
        "study_id": STUDY_ID,
        "scope": "pilot_10",
        "vivado_version": "2026.1",
        "v1_manifest_sha256": v1_digest,
        "candidate_package_sha256": package_digest,
        "v7_stability_attestation_sha256": V7_ATTESTATION_SHA,
        "expected_candidates": 10,
        "completed_candidates": len(loaded),
        "verdict": verdict,
        "criteria": criteria,
        "metrics": {
            "spearman_rho": rho,
            "median_smape": median_error,
            "rf_minus_sft_mean_mhz": paired_mean,
            "sign_reversals": reversals,
            "non_tied_pairs": non_tied,
            "candidate_smape": candidate_smape,
            "pairs": pairs,
        },
        "failures": failures,
        "generated_from": generated_from,
    }, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--check-inputs", action="store_true")
    parser.add_argument("--scope", choices=("pilot",), default=None)
    args = parser.parse_args()
    if not args.check_inputs and args.scope is None:
        parser.error("use --check-inputs or --scope pilot")
    try:
        manifest, v1_digest = verify_inputs()
        package_digest = verify_package()
        print(f"INPUTS PASS: v1={v1_digest} package={package_digest}")
        if args.scope == "pilot":
            gate, failures = build_gate(
                manifest, v1_digest, package_digest, Path(args.results))
            if gate is None:
                print("INCOMPLETE: pilot_gate.json was not written",
                      file=sys.stderr)
                for failure in failures:
                    print(f"  {failure}", file=sys.stderr)
                return 2
            output = Path(args.results) / "pilot_gate.json"
            if output.exists():
                if output.read_bytes() != canonical_json_bytes(gate):
                    raise RuntimeError(f"existing pilot gate differs: {output}")
            else:
                atomic_json(output, gate)
            print(f"{gate['verdict']}: {output}")
            return 0 if gate["verdict"] == "PASS" else 1
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
