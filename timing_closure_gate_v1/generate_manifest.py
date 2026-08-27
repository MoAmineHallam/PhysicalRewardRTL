#!/usr/bin/env python3
"""Deterministically freeze and materialize the 10-candidate closure pilot."""

import argparse
import hashlib
import json
import math
import os
import shutil
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PREREG = HERE / "preregistration.json"
MANIFEST = HERE / "manifest.json"
DIGEST = HERE / "manifest.sha256"
INPUTS = HERE / "inputs"

ARM_DIRS = {
    "sft": ("rtl/sealed_sft",),
    "rf": ("rtl/sealed_rf_s1", "rtl/sealed_rf_s2"),
    "mlp_support": ("rtl/sealed_mlp_s1",),
}
DESIGN_SALT = "closure-v1|"

WORKFLOW_FILES = (
    "timing_closure_gate_v1/README.md",
    "timing_closure_gate_v1/preregistration.json",
    "timing_closure_gate_v1/test_workflow.py",
    "timing_closure_gate_v1/generate_manifest.py",
    "timing_closure_gate_v1/closure_synth.tcl",
    "timing_closure_gate_v1/preflight_probe.sv",
    "timing_closure_gate_v1/run_preflight.py",
    "timing_closure_gate_v1/preflight/capability_preflight.json",
    "timing_closure_gate_v1/preflight_attempt1_unsupported_queries/capability_preflight.json",
    "timing_closure_gate_v1/preflight_attempt2_empty_get_timing_paths/capability_preflight.json",
    "timing_closure_gate_v1/freeze_preflight_history.py",
    "timing_closure_gate_v1/preflight_history.json",
    "timing_closure_gate_v1/run_closure.py",
    "timing_closure_gate_v1/validate_gate.py",
    "ppa_synth.tcl",
)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{lineno}: invalid JSON: {exc}")
    return rows


def design_hash(design):
    return sha256_bytes((DESIGN_SALT + design).encode("utf-8"))


def verify_file_ledger(items, label):
    for item in items:
        path = ROOT / item["path"]
        if not path.is_file() or sha256_file(path) != item["sha256"]:
            raise RuntimeError(f"{label} file missing or changed: {item['path']}")


def verify_final_preflight(preflight):
    verify_file_ledger(preflight.get("files", []), "final preflight")
    source = ROOT / preflight["source_path"]
    if sha256_file(source) != preflight["source_sha256"]:
        raise RuntimeError("final preflight source changed")
    if sha256_file(HERE / "closure_synth.tcl") != preflight["closure_tcl_sha256"]:
        raise RuntimeError("closure Tcl differs from the passing preflight")


def verify_preflight_history():
    history_path = HERE / "preflight_history.json"
    history = load_json(history_path)
    if (history.get("scope") != "preserved_synthetic_preflight_failures"
            or history.get("candidate_trials_existed") is not False
            or len(history.get("attempts", [])) != 2):
        raise RuntimeError("preflight failure history contract is invalid")
    for attempt in history["attempts"]:
        verify_file_ledger(attempt.get("files", []), attempt["directory"])
    return history_path


def load_arm_rows(directory, logical_arm):
    base = ROOT / directory
    manifest_path = base / "fmax_manifest.json"
    ppa_path = base / "ppa.jsonl"
    metadata = load_json(manifest_path)
    ppa = {row["module"]: row for row in load_jsonl(ppa_path)}
    rows = []
    for module, item in metadata.items():
        physical = ppa.get(module)
        if physical is None:
            raise RuntimeError(f"missing PPA row for {directory}/{module}")
        count = int(item.get("count", 0))
        compiled = int(physical.get("compiled", 0)) == 1
        fmax = float(physical.get("fmax_mhz", 0.0) or 0.0)
        source = base / f"{module}.sv"
        if not source.is_file():
            source = base / f"{module}.v"
        emitted_expected = str(item.get("emitted_sha256", "")).lower()
        emitted_actual = sha256_file(source) if source.is_file() else ""
        eligible = (
            count > 0
            and compiled
            and math.isfinite(fmax)
            and fmax > 0.0
            and source.is_file()
            and len(emitted_expected) == 64
            and emitted_actual == emitted_expected
        )
        rows.append({
            "logical_arm": logical_arm,
            "source_arm": Path(directory).name,
            "module": module,
            "design": item["design"],
            "family": item["family"],
            "regime": item["regime"],
            "count": count,
            "n": int(item["n"]),
            "generation_seed": int(item["generation_seed"]),
            "source_sha256": str(item.get("source_sha256", "")).lower(),
            "emitted_sha256": emitted_expected,
            "emitted_sha256_actual": emitted_actual,
            "source_path": rel(source) if source.is_file() else rel(base / f"{module}.sv"),
            "old_compiled": int(physical.get("compiled", 0)),
            "old_wns_ns": float(physical.get("wns", 0.0) or 0.0),
            "old_fmax_mhz": fmax,
            "eligible": eligible,
        })
    return rows


def weighted_mean(rows):
    denom = sum(row["count"] for row in rows)
    if denom <= 0:
        raise RuntimeError("weighted mean has no positive mass")
    return sum(row["count"] * row["old_fmax_mhz"] for row in rows) / denom


def arm_target(rows, arm):
    if arm == "sft":
        return weighted_mean(rows), {"method": "count_weighted_conditional_mean"}
    by_seed = {}
    for row in rows:
        by_seed.setdefault(row["source_arm"], []).append(row)
    seed_means = {seed: weighted_mean(seed_rows)
                  for seed, seed_rows in sorted(by_seed.items())}
    if not seed_means:
        raise RuntimeError("pooled RF selection has no eligible seed")
    target = sum(seed_means.values()) / len(seed_means)
    return target, {
        "method": "equal_seed_mean_of_count_weighted_conditional_means",
        "seed_means_mhz": seed_means,
    }


def select_candidate(rows, arm, used_source_identities):
    eligible = [row for row in rows if row["eligible"]]
    if not eligible:
        raise RuntimeError(f"no eligible {arm} candidate")
    target, detail = arm_target(eligible, arm)
    ranked = sorted(
        eligible,
        key=lambda row: (
            abs(row["old_fmax_mhz"] - target),
            row["source_sha256"],
            row["module"],
        ),
    )
    chosen = None
    for row in ranked:
        identity = row["source_sha256"] or row["emitted_sha256"]
        if identity not in used_source_identities:
            chosen = row
            used_source_identities.add(identity)
            break
    if chosen is None:
        raise RuntimeError(f"all ranked {arm} candidates duplicate a prior source")
    return chosen, target, detail, len(eligible)


def dependency_hashes():
    paths = set(WORKFLOW_FILES)
    for directories in ARM_DIRS.values():
        for directory in directories:
            paths.add(f"{directory}/fmax_manifest.json")
            paths.add(f"{directory}/ppa.jsonl")
    result = {}
    for path in sorted(paths):
        absolute = ROOT / path
        if not absolute.is_file():
            raise RuntimeError(f"required dependency missing: {path}")
        result[path] = sha256_file(absolute)
    return result


def build_manifest():
    prereg = load_json(PREREG)
    if prereg.get("study_id") != "timing_closure_gate_v1":
        raise RuntimeError("unexpected preregistration study_id")
    preflight_path = HERE / "preflight" / "capability_preflight.json"
    if not preflight_path.is_file():
        raise RuntimeError("synthetic capability preflight has not been pinned")
    preflight = load_json(preflight_path)
    if (preflight.get("scope") != "synthetic_capability_preflight"
            or preflight.get("uses_study2_candidate") is not False
            or preflight.get("verdict") != "PASS"
            or not all(preflight.get("checks", {}).values())):
        raise RuntimeError("synthetic capability preflight is not a complete PASS")
    verify_final_preflight(preflight)
    history_path = verify_preflight_history()

    all_rows = {}
    for logical_arm, directories in ARM_DIRS.items():
        rows = []
        for directory in directories:
            rows.extend(load_arm_rows(directory, logical_arm))
        all_rows[logical_arm] = rows

    support = {}
    for arm, rows in all_rows.items():
        support[arm] = {row["design"] for row in rows if row["eligible"]}
    common = sorted(support["sft"] & support["rf"] & support["mlp_support"])
    if len(common) != 15:
        raise RuntimeError(f"expected 15 common-support designs, found {len(common)}")

    family_by_design = {}
    for row in all_rows["sft"] + all_rows["rf"]:
        if row["design"] in common:
            prior = family_by_design.setdefault(row["design"], row["family"])
            if prior != row["family"]:
                raise RuntimeError(f"mixed family identity for {row['design']}")
    by_family = {}
    for design in common:
        by_family.setdefault(family_by_design[design], []).append(design)
    chosen_designs = {
        family: min(designs, key=lambda design: (design_hash(design), design))
        for family, designs in sorted(by_family.items())
    }
    expected = prereg["population"]["expected_designs"]
    actual = [chosen_designs[family] for family in sorted(chosen_designs)]
    if actual != expected:
        raise RuntimeError(f"deterministic designs {actual} != preregistered {expected}")

    used = set()
    candidates = []
    ordinal = 0
    for family in sorted(chosen_designs):
        design = chosen_designs[family]
        for arm in ("sft", "rf"):
            pool = [row for row in all_rows[arm] if row["design"] == design]
            chosen, target, detail, eligible_count = select_candidate(pool, arm, used)
            ordinal += 1
            delay_from_fmax = 1000.0 / chosen["old_fmax_mhz"]
            delay_from_wns = 5.0 - chosen["old_wns_ns"]
            if not math.isclose(delay_from_fmax, delay_from_wns,
                                rel_tol=2e-4, abs_tol=2e-3):
                raise RuntimeError(
                    f"old proxy identity mismatch for {chosen['module']}: "
                    f"{delay_from_fmax} vs {delay_from_wns}")
            candidate_id = f"c{ordinal:02d}_{family}_{arm}_{design}"
            materialized = f"timing_closure_gate_v1/inputs/{chosen['module']}.sv"
            candidates.append({
                "candidate_id": candidate_id,
                "family": family,
                "design": design,
                "arm": arm,
                "source_arm": chosen["source_arm"],
                "module": chosen["module"],
                "clock_port": "clk",
                "source_path": chosen["source_path"],
                "materialized_path": materialized,
                "source_sha256": chosen["source_sha256"],
                "emitted_sha256": chosen["emitted_sha256"],
                "count": chosen["count"],
                "n": chosen["n"],
                "generation_seed": chosen["generation_seed"],
                "old_request_period_ns": 5.0,
                "old_wns_ns": chosen["old_wns_ns"],
                "old_fmax_mhz": chosen["old_fmax_mhz"],
                "old_proxy_delay_ns": delay_from_fmax,
                "selection_target_mhz": target,
                "selection_abs_distance_mhz": abs(chosen["old_fmax_mhz"] - target),
                "eligible_candidates_in_arm_design": eligible_count,
                "selection_detail": detail,
            })

    if len(candidates) != prereg["population"]["expected_candidates"]:
        raise RuntimeError("candidate-count mismatch")
    if len({row["source_sha256"] or row["emitted_sha256"]
            for row in candidates}) != len(candidates):
        raise RuntimeError("selected source identities are not distinct")

    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v1",
        "scope": "pilot_10",
        "selection_status": "frozen_before_timing_closure",
        "capability_preflight_sha256": sha256_file(preflight_path),
        "preflight_history_sha256": sha256_file(history_path),
        "preregistration_sha256": sha256_file(PREREG),
        "legacy_metric": {
            "request_period_ns": 5.0,
            "formula": "1000/(request_period_ns-WNS)",
            "constraint_was_created_after_synthesis": True,
        },
        "common_support_designs": common,
        "design_selection_salt": DESIGN_SALT,
        "selected_designs_by_family": chosen_designs,
        "dependency_sha256": dependency_hashes(),
        "candidates": candidates,
    }


def canonical_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True)
            + "\n").encode("utf-8")


def materialize(manifest):
    INPUTS.mkdir(parents=True, exist_ok=True)
    expected_names = set()
    for row in manifest["candidates"]:
        src = ROOT / row["source_path"]
        dst = ROOT / row["materialized_path"]
        expected_names.add(dst.name)
        if sha256_file(src) != row["emitted_sha256"]:
            raise RuntimeError(f"source changed before materialization: {src}")
        if dst.exists() and dst.read_bytes() != src.read_bytes():
            raise RuntimeError(f"refusing to overwrite divergent input: {dst}")
        if not dst.exists():
            shutil.copyfile(src, dst)
        if sha256_file(dst) != row["emitted_sha256"]:
            raise RuntimeError(f"materialized hash mismatch: {dst}")
    extras = sorted(path.name for path in INPUTS.iterdir()
                    if path.is_file() and path.name not in expected_names)
    if extras:
        raise RuntimeError(f"unexpected materialized inputs: {extras}")


def write_or_refuse(manifest):
    data = canonical_bytes(manifest)
    if MANIFEST.exists() and MANIFEST.read_bytes() != data:
        raise RuntimeError(
            "manifest.json already exists and recomputation differs; preserve "
            "v1 and investigate instead of overwriting")
    if not MANIFEST.exists():
        MANIFEST.write_bytes(data)
    digest = sha256_bytes(data)
    digest_line = f"{digest}  manifest.json\n".encode("ascii")
    if DIGEST.exists() and DIGEST.read_bytes() != digest_line:
        raise RuntimeError("manifest.sha256 exists with a different digest")
    if not DIGEST.exists():
        DIGEST.write_bytes(digest_line)
    materialize(manifest)
    return digest


def check_frozen(expected):
    if not MANIFEST.is_file() or not DIGEST.is_file():
        raise RuntimeError("frozen manifest files are missing")
    expected_bytes = canonical_bytes(expected)
    if MANIFEST.read_bytes() != expected_bytes:
        raise RuntimeError("frozen manifest differs from deterministic recomputation")
    digest = sha256_bytes(MANIFEST.read_bytes())
    parts = DIGEST.read_text(encoding="ascii").split()
    if len(parts) != 2 or parts[0] != digest or parts[1] != "manifest.json":
        raise RuntimeError("manifest.sha256 is malformed or stale")
    materialize(expected)
    return digest


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true",
                      help="create the frozen manifest if absent; never overwrite divergence")
    mode.add_argument("--check", action="store_true",
                      help="recompute and verify the frozen manifest and inputs")
    args = parser.parse_args()
    try:
        expected = build_manifest()
        digest = write_or_refuse(expected) if args.write else check_frozen(expected)
    except Exception as exc:  # fail closed with one concise command-line error
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: {len(expected['candidates'])} frozen candidates")
    print(f"manifest_sha256={digest}")
    for row in expected["candidates"]:
        print(f"  {row['candidate_id']}: {row['module']} "
              f"old={row['old_fmax_mhz']:.6f} MHz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
