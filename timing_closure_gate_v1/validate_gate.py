#!/usr/bin/env python3
"""Fail-closed manifest and pilot-result validator."""

import argparse
import hashlib
import json
import math
import os
import statistics
import sys
from pathlib import Path

try:
    from . import generate_manifest as gm
except ImportError:
    import generate_manifest as gm


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESULTS = HERE / "results"


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    os.replace(temp, path)


def rankdata(values):
    order = sorted(range(len(values)), key=lambda index: (values[index], index))
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        average_rank = 0.5 * ((cursor + 1) + end)
        for position in range(cursor, end):
            ranks[order[position]] = average_rank
        cursor = end
    return ranks


def pearson(x, y):
    if len(x) != len(y) or len(x) < 2:
        return None
    mx, my = statistics.fmean(x), statistics.fmean(y)
    dx = [value - mx for value in x]
    dy = [value - my for value in y]
    denom = math.sqrt(sum(value * value for value in dx)
                      * sum(value * value for value in dy))
    if denom == 0.0:
        return None
    return sum(a * b for a, b in zip(dx, dy)) / denom


def spearman(x, y):
    return pearson(rankdata(x), rankdata(y))


def smape(a, b):
    denom = 0.5 * (abs(a) + abs(b))
    return 0.0 if denom == 0.0 else abs(a - b) / denom


def static_tcl_order_check():
    lines = (HERE / "closure_synth.tcl").read_text(encoding="utf-8").splitlines()
    code = [line.strip() for line in lines
            if line.strip() and not line.lstrip().startswith("#")]
    read_indices = [index for index, line in enumerate(code)
                    if line.startswith("read_xdc ")]
    synth_indices = [index for index, line in enumerate(code)
                     if line.startswith("synth_design ")]
    if len(read_indices) != 1 or len(synth_indices) != 1:
        raise RuntimeError("closure_synth.tcl must contain one read_xdc and synth_design")
    if read_indices[0] >= synth_indices[0]:
        raise RuntimeError("clock XDC is not read before synthesis")


def check_manifest():
    expected = gm.build_manifest()
    digest = gm.check_frozen(expected)
    prereg = json.loads((HERE / "preregistration.json").read_text(encoding="utf-8"))
    legacy = ROOT / prereg["immutability"]["legacy_ppa_synth_path"]
    if sha256_file(legacy) != prereg["immutability"]["legacy_ppa_synth_sha256_raw"]:
        raise RuntimeError("legacy ppa_synth.tcl changed after preregistration")
    static_tcl_order_check()
    for path, frozen_hash in expected["dependency_sha256"].items():
        if sha256_file(ROOT / path) != frozen_hash:
            raise RuntimeError(f"dependency changed after manifest freeze: {path}")
    for candidate in expected["candidates"]:
        if sha256_file(ROOT / candidate["materialized_path"]) != candidate["emitted_sha256"]:
            raise RuntimeError(f"materialized input mismatch: {candidate['candidate_id']}")
    return expected, digest


def load_candidate_result(candidate, digest, results_dir):
    path = results_dir / candidate["candidate_id"] / "closure_result.json"
    if not path.is_file():
        return None, path, ["result_missing"]
    errors = []
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, path, [f"invalid_result_json:{exc}"]
    expected_identity = {
        "study_id": "timing_closure_gate_v1",
        "scope": "pilot_10",
        "manifest_sha256": digest,
        "candidate_id": candidate["candidate_id"],
        "family": candidate["family"],
        "design": candidate["design"],
        "arm": candidate["arm"],
        "module": candidate["module"],
    }
    for key, expected in expected_identity.items():
        if result.get(key) != expected:
            errors.append(f"{key}_mismatch")
    if not math.isclose(float(result.get("old_fmax_mhz", math.nan)),
                        float(candidate["old_fmax_mhz"]),
                        rel_tol=1e-12, abs_tol=1e-12):
        errors.append("old_fmax_mismatch")
    if result.get("status") == "COMPLETE":
        closure = float(result.get("closure_fmax_mhz", math.nan))
        width = float(result.get("relative_bracket_width", math.inf))
        tight = float(result.get("tight_failing_period_ns", math.nan))
        loose = float(result.get("loose_passing_period_ns", math.nan))
        if not math.isfinite(closure) or closure <= 0.0:
            errors.append("invalid_closure_frequency")
        if not math.isfinite(width) or width > 0.01 + 1e-12:
            errors.append("bracket_tolerance_failed")
        if not (math.isfinite(tight) and math.isfinite(loose)
                and 1.0 <= tight < loose <= 200.0):
            errors.append("invalid_period_bracket")
        purposes = [row.get("purpose") for row in result.get("trials", [])]
        if "confirm_fail" not in purposes or "confirm_pass" not in purposes:
            errors.append("boundary_confirmation_missing")
    elif result.get("status") == "FAILED":
        if float(result.get("closure_fmax_mhz", math.nan)) != 0.0:
            errors.append("failed_candidate_not_zero_scored")
        if not result.get("failure_reason"):
            errors.append("failure_reason_missing")
    else:
        errors.append("unknown_status")
    return result, path, errors


def sign(value, tolerance=0.0):
    if abs(value) <= tolerance:
        return 0
    return 1 if value > 0.0 else -1


def build_pilot_gate(manifest, digest, results_dir):
    loaded = []
    failures = []
    generated_from = [{
        "path": "timing_closure_gate_v1/manifest.json",
        "sha256": digest,
    }]
    for candidate in manifest["candidates"]:
        result, path, errors = load_candidate_result(candidate, digest, results_dir)
        if result is None:
            failures.append({"candidate_id": candidate["candidate_id"],
                             "errors": errors})
            continue
        loaded.append((candidate, result))
        generated_from.append({
            "path": path.resolve().relative_to(ROOT).as_posix(),
            "sha256": sha256_file(path),
        })
        if errors:
            failures.append({"candidate_id": candidate["candidate_id"],
                             "errors": errors})

    if len(loaded) != 10:
        return None, failures

    complete = (not failures
                and all(result["status"] == "COMPLETE"
                        for _, result in loaded))
    old = [float(candidate["old_fmax_mhz"]) for candidate, _ in loaded]
    closure = [float(result["closure_fmax_mhz"]) for _, result in loaded]
    rho = spearman(old, closure)
    errors = [smape(a, b) for a, b in zip(old, closure)]
    median_error = statistics.median(errors)

    by_design = {}
    for candidate, result in loaded:
        by_design.setdefault(candidate["design"], {})[candidate["arm"]] = (
            candidate, result)
    pair_differences = []
    reversals = 0
    non_tied = 0
    pair_rows = []
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
        pair_differences.append(closure_diff)
        old_scale = 0.5 * (abs(float(rf_c["old_fmax_mhz"]))
                           + abs(float(sft_c["old_fmax_mhz"])))
        old_sign = sign(old_diff, tolerance=0.01 * old_scale)
        closure_sign = sign(closure_diff)
        reversed_pair = old_sign != 0 and closure_sign != old_sign
        non_tied += int(old_sign != 0)
        reversals += int(reversed_pair)
        pair_rows.append({
            "design": design,
            "old_rf_minus_sft_mhz": old_diff,
            "closure_rf_minus_sft_mhz": closure_diff,
            "old_proxy_tie": old_sign == 0,
            "sign_reversal": reversed_pair,
        })
    paired_mean = statistics.fmean(pair_differences) if pair_differences else None

    criteria = {
        "complete_and_constrained": bool(complete and len(pair_rows) == 5),
        "spearman_ge_0_90": bool(rho is not None and rho >= 0.90),
        "median_smape_le_0_15": bool(median_error <= 0.15),
        "paired_direction": bool(paired_mean is not None
                                  and paired_mean > 0.0 and reversals <= 1),
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    if verdict == "FAIL" and not failures:
        failures.append({"gate": "threshold_failure",
                         "failed_criteria": [key for key, ok in criteria.items()
                                             if not ok]})
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v1",
        "scope": "pilot_10",
        "manifest_sha256": digest,
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
            "candidate_smape": errors,
            "pairs": pair_rows,
        },
        "failures": failures,
        "generated_from": generated_from,
    }, failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-manifest", action="store_true")
    parser.add_argument("--scope", choices=("pilot",), default=None)
    parser.add_argument("--results", default=str(RESULTS))
    args = parser.parse_args()
    if not args.check_manifest and args.scope is None:
        parser.error("use --check-manifest or --scope pilot")
    try:
        manifest, digest = check_manifest()
        print(f"MANIFEST PASS: {digest}")
        if args.scope == "pilot":
            gate, failures = build_pilot_gate(
                manifest, digest, Path(args.results))
            if gate is None:
                print("INCOMPLETE: pilot_gate.json was not written", file=sys.stderr)
                for failure in failures:
                    print(f"  {failure}", file=sys.stderr)
                return 2
            output = Path(args.results) / "pilot_gate.json"
            atomic_json(output, gate)
            print(f"{gate['verdict']}: {output}")
            return 0 if gate["verdict"] == "PASS" else 1
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

