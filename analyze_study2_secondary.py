#!/usr/bin/env python3
"""Bounded, artifact-derived secondary analysis for sealed Study 2.

The preregistered RF-versus-SFT outcome in ``sealed_results_study2.json`` is
immutable.  This script performs only the post-primary analyses frozen in
``study2_secondary_analysis_spec.json``:

* a direct paired RF-minus-MLP comparison on the same zero-penalized endpoint;
* conditional LUT/FF/DSP/BRAM/vectorless-power summaries on three-arm common
  support; and
* reviewer-requested, explicitly post-primary family, sensitivity, sealed-
  support, and illustrative source-level diagnostics; and
* generated claim ledgers and TeX tables with file:line provenance.

No candidate is selected and no sample is added or removed from the primary
endpoint.  Incorrect samples and implementation failures remain 0 MHz for
Fmax.  Area and power are never assigned zero for failure, because that would
reward failure; those diagnostics condition on compiled, oracle-correct draws.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import pathlib
import sys
from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np

from analyze_sealed_v3 import (
    BOOT_SEED,
    CI,
    N_BOOT,
    bootstrap_ci,
    load_eval_dir,
    load_sealed,
    make_bootstrap_plans,
    validate_generation_config,
)
from verify_sealed_ppa import verify_directory


ROOT = pathlib.Path(__file__).resolve().parent
SPEC_PATH = ROOT / "study2_secondary_analysis_spec.json"
SEALED_PATH = ROOT / "sealed_split.json"
PRIMARY_RESULT_PATH = ROOT / "sealed_results_study2.json"
PREREG_PATH = ROOT / "preregistration.json"
PREREG_STUDY2_PATH = ROOT / "preregistration_study2.json"
PPA_AUDIT_PATH = ROOT / "sealed_ppa_audit_study2.json"
OUTPUT_PATH = ROOT / "study2_secondary_results.json"
GENERATED = ROOT / "paper" / "generated"

ARM_DIRS = collections.OrderedDict(
    (
        ("sft", ((ROOT / "rtl" / "sealed_sft", 48, "sft"),)),
        (
            "rf",
            (
                (ROOT / "rtl" / "sealed_rf_s1", 24, "rf_s1"),
                (ROOT / "rtl" / "sealed_rf_s2", 24, "rf_s2"),
            ),
        ),
        (
            "mlp",
            (
                (ROOT / "rtl" / "sealed_mlp_s1", 24, "mlp_s1"),
                (ROOT / "rtl" / "sealed_mlp_s2", 24, "mlp_s2"),
            ),
        ),
    )
)
ALL_AUDIT_DIRS = (
    ROOT / "rtl" / "sealed_sft",
    ROOT / "rtl" / "sealed_rf_s1",
    ROOT / "rtl" / "sealed_rf_s2",
    ROOT / "rtl" / "sealed_rf_mid_s1",
    ROOT / "rtl" / "sealed_rf_mid_s2",
    ROOT / "rtl" / "sealed_mlp_s1",
    ROOT / "rtl" / "sealed_mlp_s2",
    ROOT / "rtl" / "sealed_corr_s1",
)
METRICS = ("lut", "ff", "dsp", "bram", "power_w")
SCOPES = ("interp", "extrap", "all")
FAMILY_LABELS = collections.OrderedDict(
    (("fir", "Fir"), ("firr", "ReverseFir"), ("poly", "Polynomial"),
     ("iir", "Recursive"), ("med", "Median"))
)


class SecondaryAnalysisError(RuntimeError):
    pass


@dataclass(frozen=True)
class Candidate:
    module: str
    design: str
    count: int
    compiled: bool
    fmax: float
    resources: dict[str, float | None]
    manifest_source: str
    ppa_source: str


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def nlines(path: pathlib.Path) -> int:
    with path.open(encoding="utf-8") as stream:
        return sum(1 for _ in stream)


def span(path: pathlib.Path) -> str:
    return f"{rel(path)}:1-{nlines(path)}"


def sha256_lf(path: pathlib.Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def read_json(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SecondaryAnalysisError(f"cannot read valid JSON {rel(path)}: {exc}") from exc


def finite(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SecondaryAnalysisError(f"{label} is not numeric: {value!r}") from exc
    if not math.isfinite(result) or result < 0:
        raise SecondaryAnalysisError(f"{label} is not finite and nonnegative: {value!r}")
    return result


def manifest_lines(path: pathlib.Path) -> dict[str, int]:
    found = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith('"') and stripped.endswith((': {', '": {')):
            module = stripped.split('"', 2)[1]
            if "__" in module:
                found[module] = lineno
    return found


def verify_frozen_inputs(spec: dict) -> None:
    expected = spec.get("inputs_sha256_lf")
    if not isinstance(expected, dict):
        raise SecondaryAnalysisError("secondary specification lacks inputs_sha256_lf")
    for name, digest in expected.items():
        path = ROOT / name
        if not path.is_file():
            raise SecondaryAnalysisError(f"frozen input is missing: {name}")
        actual = sha256_lf(path)
        if actual != digest:
            raise SecondaryAnalysisError(
                f"frozen input hash mismatch for {name}: {actual} != {digest}"
            )
    if spec.get("immutable_primary_outcome") != "full_two_regime_repair":
        raise SecondaryAnalysisError("secondary specification changed the primary outcome")


def validate_configs() -> None:
    validate_generation_config(
        str(ROOT / "rtl" / "sealed_sft"),
        policy="sft", training_seed=0, generation_seed=100, n=48,
        score_rf=True, checkpoint="sft_v6c_out",
    )
    for seed in (1, 2):
        validate_generation_config(
            str(ROOT / "rtl" / f"sealed_rf_s{seed}"),
            policy=f"rf_s{seed}", training_seed=seed,
            generation_seed=100 + seed, n=24, score_rf=True,
            checkpoint=f"grpo_rf_s{seed}/upd_276",
        )
        validate_generation_config(
            str(ROOT / "rtl" / f"sealed_mlp_s{seed}"),
            policy=f"mlp_s{seed}", training_seed=seed,
            generation_seed=100 + seed, n=24, score_rf=False,
            checkpoint=f"grpo_mlp_s{seed}/upd_276",
        )


def verify_ppa_audit(audit: dict) -> dict:
    if audit.get("schema") != "sealed_ppa_audit/1" or audit.get("complete") is not True:
        raise SecondaryAnalysisError("sealed PPA audit is not complete")
    frozen = {pathlib.Path(row["directory"]).name: row for row in audit.get("directories", [])}
    if set(frozen) != {path.name for path in ALL_AUDIT_DIRS}:
        raise SecondaryAnalysisError("sealed PPA audit directory set changed")
    checked = []
    for directory in ALL_AUDIT_DIRS:
        row = verify_directory(str(directory))
        expected = frozen[directory.name]
        for field in ("manifest_sha256", "ppa_sha256", "n_candidates", "n_compiled", "n_failed"):
            if row[field] != expected[field]:
                raise SecondaryAnalysisError(
                    f"PPA audit mismatch for {directory.name}/{field}: "
                    f"{row[field]!r} != {expected[field]!r}"
                )
        checked.append({k: row[k] for k in row if k != "directory"} | {"directory": rel(directory)})
    total = sum(row["n_candidates"] for row in checked)
    compiled = sum(row["n_compiled"] for row in checked)
    failed = sum(row["n_failed"] for row in checked)
    if (total, compiled, failed) != (489, 488, 1):
        raise SecondaryAnalysisError(
            f"expected complete 489/488/1 PPA audit, got {total}/{compiled}/{failed}"
        )
    return {"total": total, "compiled": compiled, "failed": failed, "directories": checked}


def load_seed(
    directory: pathlib.Path,
    expected_n: int,
    expected_policy: str,
    designs: list[str],
    meta: dict[str, tuple[str, str]],
) -> tuple[dict[str, dict], list[str]]:
    # Reuse the frozen loader as an independent fail-closed validation of
    # generation denominators, rewards, PPA completeness, and zero-correct designs.
    frozen_rows = load_eval_dir(
        str(directory), designs, meta, expected_n,
        require_reward=expected_policy == "sft" or expected_policy.startswith("rf_"),
    )
    manifest_path = directory / "fmax_manifest.json"
    ppa_path = directory / "ppa.jsonl"
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise SecondaryAnalysisError(f"{rel(manifest_path)} is not an object")
    mlines = manifest_lines(manifest_path)
    ppa = {}
    plines = {}
    for lineno, line in enumerate(ppa_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        module = row.get("module")
        if not isinstance(module, str) or module in ppa:
            raise SecondaryAnalysisError(f"invalid or duplicate PPA module at {rel(ppa_path)}:{lineno}")
        ppa[module] = row
        plines[module] = lineno
    if set(ppa) != set(manifest):
        raise SecondaryAnalysisError(f"manifest/PPA module set differs in {rel(directory)}")

    grouped: dict[str, list[Candidate]] = collections.defaultdict(list)
    for module, info in manifest.items():
        if info.get("policy") != expected_policy:
            raise SecondaryAnalysisError(
                f"policy mismatch for {module}: {info.get('policy')!r} != {expected_policy!r}"
            )
        design = info.get("design")
        if design not in meta:
            raise SecondaryAnalysisError(f"unknown sealed design for {module}: {design!r}")
        count = int(info.get("count", 0))
        n = int(info.get("n", info.get("n_samples", 0)))
        if count <= 0 or n != expected_n:
            raise SecondaryAnalysisError(f"invalid count/n for {module}: {count}/{n}")
        row = ppa[module]
        compiled = bool(row.get("compiled"))
        fmax = finite(row.get("fmax_mhz", 0.0), f"{module} Fmax") if compiled else 0.0
        resources = {}
        for metric in METRICS:
            resources[metric] = (
                finite(row.get(metric), f"{module} {metric}") if compiled else None
            )
        grouped[design].append(
            Candidate(
                module=module, design=design, count=count, compiled=compiled,
                fmax=fmax, resources=resources,
                manifest_source=f"{rel(manifest_path)}:{mlines.get(module, 1)}",
                ppa_source=f"{rel(ppa_path)}:{plines[module]}",
            )
        )

    rows = {}
    for design in designs:
        candidates = grouped.get(design, [])
        correct = sum(candidate.count for candidate in candidates)
        compiled = sum(candidate.count for candidate in candidates if candidate.compiled)
        if correct > expected_n or compiled > correct:
            raise SecondaryAnalysisError(
                f"sample multiplicity overflow for {expected_policy}/{design}"
            )
        weighted_fmax = sum(candidate.count * candidate.fmax for candidate in candidates)
        resources = {}
        for metric in METRICS:
            resources[metric] = (
                sum(
                    candidate.count * float(candidate.resources[metric])
                    for candidate in candidates if candidate.compiled
                ) / compiled
                if compiled else None
            )
        sources = sorted(
            {candidate.manifest_source for candidate in candidates}
            | {candidate.ppa_source for candidate in candidates}
        )
        rows[design] = {
            "n": expected_n,
            "correct": correct,
            "compiled": compiled,
            "equal": weighted_fmax / expected_n,
            "correct_rate": correct / expected_n,
            "synth_rate": compiled / expected_n,
            "resources": resources,
            "sources": sources,
        }
        for field in ("equal", "correct_rate", "synth_rate"):
            if not math.isclose(rows[design][field], frozen_rows[design][field], abs_tol=1e-10):
                raise SecondaryAnalysisError(
                    f"independent loader disagrees for {expected_policy}/{design}/{field}"
                )
    return rows, [span(manifest_path), span(ppa_path), span(directory / "holdout_summary.json")]


def combine_seeds(seed_rows: list[dict[str, dict]], designs: list[str]) -> dict[str, dict]:
    combined = {}
    for design in designs:
        rows = [seed[design] for seed in seed_rows]
        total_n = sum(row["n"] for row in rows)
        correct = sum(row["correct"] for row in rows)
        compiled = sum(row["compiled"] for row in rows)
        resources = {}
        for metric in METRICS:
            resources[metric] = (
                sum(
                    row["compiled"] * float(row["resources"][metric])
                    for row in rows if row["compiled"]
                ) / compiled
                if compiled else None
            )
        combined[design] = {
            "n": total_n,
            "correct": correct,
            "compiled": compiled,
            "equal": sum(row["equal"] * row["n"] for row in rows) / total_n,
            "correct_rate": correct / total_n,
            "synth_rate": compiled / total_n,
            "resources": resources,
            "sources": sorted({source for row in rows for source in row["sources"]}),
        }
    return combined


def load_arms(
    designs: list[str], meta: dict[str, tuple[str, str]], primary: dict
) -> tuple[dict[str, dict[str, dict]], dict[str, list[str]]]:
    arms = {}
    sources = {}
    for arm, specs in ARM_DIRS.items():
        seed_rows = []
        arm_sources = []
        for directory, expected_n, expected_policy in specs:
            rows, seed_sources = load_seed(
                directory, expected_n, expected_policy, designs, meta
            )
            seed_rows.append(rows)
            arm_sources.extend(seed_sources)
        arms[arm] = combine_seeds(seed_rows, designs)
        sources[arm] = sorted(set(arm_sources))
        for design in designs:
            frozen = primary["sft"][design] if arm == "sft" else primary["arms"][arm][design]
            for field in ("equal", "correct_rate", "synth_rate"):
                if not math.isclose(arms[arm][design][field], frozen[field], abs_tol=1e-10):
                    raise SecondaryAnalysisError(
                        f"derived {arm}/{design}/{field} disagrees with sealed primary result"
                    )
    return arms, sources


def scoped_designs(
    designs: Iterable[str], meta: dict[str, tuple[str, str]], scope: str
) -> list[str]:
    return [design for design in designs if scope == "all" or meta[design][1] == scope]


def direct_comparison(
    arms: dict[str, dict[str, dict]],
    designs: list[str],
    meta: dict[str, tuple[str, str]],
    primary: dict,
) -> dict:
    plans = make_bootstrap_plans(designs, meta, n_boot=N_BOOT, seed=BOOT_SEED)
    expected_hashes = primary["bootstrap"]["plan_sha256"]
    if {scope: plan.digest for scope, plan in plans.items()} != expected_hashes:
        raise SecondaryAnalysisError("reconstructed primary bootstrap plan hash changed")
    result = {}
    for scope in SCOPES:
        selected = scoped_designs(designs, meta, scope)
        diffs = {
            design: arms["rf"][design]["equal"] - arms["mlp"][design]["equal"]
            for design in selected
        }
        mean, lo, hi = bootstrap_ci(diffs, plans[scope], ci=CI)
        result[scope] = {
            "n_designs": len(selected),
            "sft_equal": float(np.mean([arms["sft"][d]["equal"] for d in selected])),
            "mlp_equal": float(np.mean([arms["mlp"][d]["equal"] for d in selected])),
            "rf_equal": float(np.mean([arms["rf"][d]["equal"] for d in selected])),
            "rf_minus_mlp": mean,
            "ci_lo": lo,
            "ci_hi": hi,
            "ci_excludes_zero": bool(lo > 0 or hi < 0),
            "rf_correct": float(np.mean([arms["rf"][d]["correct_rate"] for d in selected])),
            "mlp_correct": float(np.mean([arms["mlp"][d]["correct_rate"] for d in selected])),
            "rf_synth_rate": float(np.mean([arms["rf"][d]["synth_rate"] for d in selected])),
            "mlp_synth_rate": float(np.mean([arms["mlp"][d]["synth_rate"] for d in selected])),
            "bootstrap_plan_sha256": plans[scope].digest,
        }
    return result


def resource_summary(
    arms: dict[str, dict[str, dict]],
    designs: list[str],
    meta: dict[str, tuple[str, str]],
) -> dict:
    support = [
        design for design in designs
        if all(arms[arm][design]["compiled"] > 0 for arm in ARM_DIRS)
    ]
    if not support:
        raise SecondaryAnalysisError("three-arm resource common support is empty")
    plans = make_bootstrap_plans(support, meta, n_boot=N_BOOT, seed=BOOT_SEED)
    result = {
        "conditioning": (
            "multiplicity-weighted within design over compiled oracle-correct draws; "
            "equal-weighted over designs with compiled correct support in SFT, RF, and MLP"
        ),
        "power_limitation": "Vivado vectorless estimate; not measured board power",
        "common_support_designs": support,
        "n_common_support": len(support),
        "bootstrap_plan_sha256": {scope: plan.digest for scope, plan in plans.items()},
        "metrics": {},
    }
    for metric in METRICS:
        scopes = {}
        for scope in SCOPES:
            selected = scoped_designs(support, meta, scope)
            means = {
                arm: float(np.mean([arms[arm][d]["resources"][metric] for d in selected]))
                for arm in ARM_DIRS
            }
            comparisons = {}
            for label, left, right in (
                ("rf_minus_sft", "rf", "sft"),
                ("rf_minus_mlp", "rf", "mlp"),
            ):
                diffs = {
                    design: float(arms[left][design]["resources"][metric])
                    - float(arms[right][design]["resources"][metric])
                    for design in selected
                }
                mean, lo, hi = bootstrap_ci(diffs, plans[scope], ci=CI)
                comparisons[label] = {
                    "mean_diff": mean,
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "ci_excludes_zero": bool(lo > 0 or hi < 0),
                }
            scopes[scope] = {
                "n_designs": len(selected),
                "means": means,
                "rf_over_sft": means["rf"] / means["sft"] if means["sft"] else None,
                "rf_over_mlp": means["rf"] / means["mlp"] if means["mlp"] else None,
                "comparisons": comparisons,
            }
        result["metrics"][metric] = scopes
    return result


def coverage(arms: dict[str, dict[str, dict]], designs: list[str]) -> dict:
    out = {}
    for arm, rows in arms.items():
        total_n = sum(rows[d]["n"] for d in designs)
        correct = sum(rows[d]["correct"] for d in designs)
        compiled = sum(rows[d]["compiled"] for d in designs)
        out[arm] = {
            "samples": total_n,
            "correct": correct,
            "compiled": compiled,
            "correct_rate": correct / total_n,
            "synth_rate": compiled / total_n,
            "designs_with_compiled_correct": sum(rows[d]["compiled"] > 0 for d in designs),
        }
    return out


def reviewer_family_breakdown(
    arms: dict[str, dict[str, dict]],
    designs: list[str],
    meta: dict[str, tuple[str, str]],
) -> dict:
    """Descriptive sealed family point estimates; no family-level inference."""
    out = collections.OrderedDict()
    for family in FAMILY_LABELS:
        selected = [design for design in designs if meta[design][0] == family]
        if not selected:
            raise SecondaryAnalysisError(f"sealed family is empty: {family}")
        sft = float(np.mean([arms["sft"][design]["equal"] for design in selected]))
        rf = float(np.mean([arms["rf"][design]["equal"] for design in selected]))
        out[family] = {
            "n_designs": len(selected),
            "n_interp": sum(meta[design][1] == "interp" for design in selected),
            "n_extrap": sum(meta[design][1] == "extrap" for design in selected),
            "sft_equal": sft,
            "rf_equal": rf,
            "rf_minus_sft": rf - sft,
            "designs": selected,
        }
    return out


def reviewer_sensitivity(
    arms: dict[str, dict[str, dict]],
    designs: list[str],
    meta: dict[str, tuple[str, str]],
    spec: dict,
) -> dict:
    """Post-review sensitivity analyses that leave the frozen primary intact."""
    cfg = spec["reviewer_requested_analyses"]["unstratified_sensitivity"]
    n_boot = int(cfg["bootstrap_replicates"])
    seed = int(cfg["bootstrap_seed"])
    diffs = np.asarray(
        [arms["rf"][design]["equal"] - arms["sft"][design]["equal"]
         for design in designs],
        dtype=float,
    )
    rng = np.random.default_rng(seed)
    sampled = diffs[rng.integers(0, len(diffs), size=(n_boot, len(diffs)))]
    boot_means = sampled.mean(axis=1)
    alpha = (1.0 - CI) / 2.0
    unstratified = {
        "n_designs": len(designs),
        "n_boot": n_boot,
        "seed": seed,
        "interval": "percentile",
        "mean_diff": float(diffs.mean()),
        "ci_lo": float(np.quantile(boot_means, alpha)),
        "ci_hi": float(np.quantile(boot_means, 1.0 - alpha)),
    }
    omissions = collections.OrderedDict()
    for family in FAMILY_LABELS:
        kept = [
            arms["rf"][design]["equal"] - arms["sft"][design]["equal"]
            for design in designs if meta[design][0] != family
        ]
        omissions[family] = float(np.mean(kept))
    return {
        "unstratified_paired_bootstrap": unstratified,
        "leave_one_family_out": {
            "effects": omissions,
            "minimum": min(omissions.values()),
            "maximum": max(omissions.values()),
        },
    }


def _candidate_inventory(directories: list[pathlib.Path]) -> tuple[dict, list[str]]:
    """Merge identical raw candidate strings across seeds by source hash."""
    inventory: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    sources: list[str] = []
    for directory in directories:
        manifest_path = directory / "fmax_manifest.json"
        ppa_path = directory / "ppa.jsonl"
        manifest = read_json(manifest_path)
        ppa_rows = {
            row["module"]: row
            for row in (
                json.loads(line) for line in ppa_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        for module, info in manifest.items():
            design = info["design"]
            source_hash = info["source_sha256"]
            row = ppa_rows[module]
            fmax = float(row["fmax_mhz"]) if row.get("compiled") else 0.0
            entry = inventory[design].setdefault(
                source_hash,
                {"count": 0, "fmax": fmax, "modules": []},
            )
            if not math.isclose(entry["fmax"], fmax, abs_tol=1e-9):
                raise SecondaryAnalysisError(
                    f"identical source hash has inconsistent Fmax for {design}/{source_hash}"
                )
            entry["count"] += int(info["count"])
            entry["modules"].append(module)
        sources.extend((span(manifest_path), span(ppa_path)))
    return inventory, sorted(set(sources))


def reviewer_sealed_support(designs: list[str]) -> tuple[dict, list[str]]:
    sft, sft_sources = _candidate_inventory([ROOT / "rtl" / "sealed_sft"])
    rf, rf_sources = _candidate_inventory(
        [ROOT / "rtl" / "sealed_rf_s1", ROOT / "rtl" / "sealed_rf_s2"]
    )
    common = [design for design in designs if sft.get(design) and rf.get(design)]
    if not common:
        raise SecondaryAnalysisError("sealed SFT/RF correct-support intersection is empty")
    support_count = 0
    effective = {"sft": [], "rf": []}
    exceptions = []
    for design in common:
        sft_max = max(row["fmax"] for row in sft[design].values())
        rf_total = sum(row["count"] for row in rf[design].values())
        rf_conditional = sum(
            row["count"] * row["fmax"] for row in rf[design].values()
        ) / rf_total
        supported = sft_max >= rf_conditional - 1e-6
        support_count += int(supported)
        if not supported:
            exceptions.append(design)
        for arm, inventory in (("sft", sft), ("rf", rf)):
            counts = np.asarray(
                [row["count"] for row in inventory[design].values()], dtype=float
            )
            probabilities = counts / counts.sum()
            effective[arm].append(float(1.0 / np.sum(probabilities ** 2)))
    return {
        "common_correct_support_designs": len(common),
        "sft_support_at_or_above_rf_conditional": support_count,
        "exceptions": exceptions,
        "sft_effective_support": float(np.mean(effective["sft"])),
        "rf_effective_support": float(np.mean(effective["rf"])),
        "identity": "source_sha256 merges identical raw candidate strings across seeds",
    }, sorted(set(sft_sources + rf_sources))


def reviewer_rtl_case(spec: dict) -> tuple[dict, list[str]]:
    cfg = spec["reviewer_requested_analyses"]["illustrative_rtl_case"]
    design = cfg["design"]
    selected = {
        "sft": (ROOT / "rtl" / "sealed_sft", cfg["sft_candidate"]),
        "rf": (ROOT / "rtl" / "sealed_rf_s1", cfg["rf_candidate"]),
    }
    out = {"design": design, "selection_status": cfg["selection_status"], "arms": {}}
    sources = [span(SPEC_PATH)]
    for arm, (directory, module) in selected.items():
        manifest_path = directory / "fmax_manifest.json"
        ppa_path = directory / "ppa.jsonl"
        rtl_path = directory / f"{module}.sv"
        manifest = read_json(manifest_path)
        if module not in manifest or manifest[module]["design"] != design:
            raise SecondaryAnalysisError(f"illustrative candidate mismatch: {module}")
        ppa_rows = {
            row["module"]: row
            for row in (
                json.loads(line) for line in ppa_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        row = ppa_rows[module]
        if not row.get("compiled"):
            raise SecondaryAnalysisError(f"illustrative candidate did not compile: {module}")
        counts = [
            int(info["count"]) for info in manifest.values()
            if info["design"] == design
        ]
        if int(manifest[module]["count"]) != max(counts):
            raise SecondaryAnalysisError(f"illustrative candidate is not dominant: {module}")
        rtl = rtl_path.read_text(encoding="utf-8")
        if arm == "sft":
            structural_check = all(token in rtl for token in ("xs [0:12]", "p  [0:12]", "y <= p[0] + p[1]"))
            structure = "direct form with delayed samples, product registers, and a final parallel sum"
        else:
            structural_check = all(token in rtl for token in ("a0, a1", "a0 <= 8'd19 * x + a1", "a12 <= 8'd37 * x"))
            structure = "registered transposed accumulation chain"
        if not structural_check:
            raise SecondaryAnalysisError(f"illustrative structural check failed: {module}")
        out["arms"][arm] = {
            "module": module,
            "count": int(manifest[module]["count"]),
            "n": int(manifest[module]["n"]),
            "sample_mass": int(manifest[module]["count"]) / int(manifest[module]["n"]),
            "fmax": float(row["fmax_mhz"]),
            "lut": int(row["lut"]),
            "ff": int(row["ff"]),
            "dsp": int(row["dsp"]),
            "structure": structure,
        }
        sources.extend((span(manifest_path), span(ppa_path), span(rtl_path)))
    return out, sorted(set(sources))


class Claims:
    def __init__(self) -> None:
        self.data: collections.OrderedDict[str, dict] = collections.OrderedDict()

    def add(
        self, key: str, value: Any, display: str, unit: str,
        method: str, sources: Iterable[str],
    ) -> None:
        if not key.isalpha() or key in self.data:
            raise SecondaryAnalysisError(f"invalid or duplicate claim ID: {key}")
        source_list = sorted(set(sources))
        if not source_list:
            raise SecondaryAnalysisError(f"claim has no provenance: {key}")
        self.data[key] = {
            "value": value, "display": display, "unit": unit,
            "method": method, "sources": source_list,
        }


def fmt(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}"


def build_claims(
    primary: dict,
    direct: dict,
    resources: dict,
    cov: dict,
    ppa: dict,
    arm_sources: dict[str, list[str]],
    family: dict,
    sensitivity: dict,
    sealed_support: dict,
    rtl_case: dict,
    reviewer_sources: dict[str, list[str]],
) -> Claims:
    claims = Claims()
    direct_sources = sorted(set(arm_sources["sft"] + arm_sources["rf"] + arm_sources["mlp"]))
    ppa_sources = direct_sources + [span(PPA_AUDIT_PATH)]
    claims.add("StudyTwoDesignCount", direct["all"]["n_designs"],
               str(direct["all"]["n_designs"]), "designs",
               "Count sealed designs in the frozen direct comparison.", direct_sources)
    claims.add("StudyTwoPpaCandidates", ppa["total"], str(ppa["total"]), "candidates",
               "Sum complete candidate PPA rows across all frozen Study 2 arms.",
               [span(PPA_AUDIT_PATH)])
    claims.add("StudyTwoPpaCompiled", ppa["compiled"], str(ppa["compiled"]), "candidates",
               "Count successful Vivado implementations in the complete audit.",
               [span(PPA_AUDIT_PATH)])
    claims.add("StudyTwoPpaFailed", ppa["failed"], str(ppa["failed"]), "candidates",
               "Count explicit Vivado implementation failures in the complete audit.",
               [span(PPA_AUDIT_PATH)])

    primary_source = [span(PRIMARY_RESULT_PATH)]
    primary_prefixes = {"interp": "Interp", "extrap": "Extrap", "all": "Overall"}
    for scope, prefix in primary_prefixes.items():
        row = primary["report"]["rf"]["combined"][scope]
        claims.add(f"StudyTwo{prefix}RfSftGain", row["mean_diff"],
                   fmt(row["mean_diff"]), "MHz",
                   "Preregistered paired RF-minus-SFT penalized equal-sample Fmax effect.",
                   primary_source)
        claims.add(f"StudyTwo{prefix}RfSftCiLow", row["ci_lo"],
                   fmt(row["ci_lo"]), "MHz",
                   "Preregistered stratified paired-bootstrap lower bound for RF minus SFT.",
                   primary_source)
        claims.add(f"StudyTwo{prefix}RfSftCiHigh", row["ci_hi"],
                   fmt(row["ci_hi"]), "MHz",
                   "Preregistered stratified paired-bootstrap upper bound for RF minus SFT.",
                   primary_source)
        claims.add(f"StudyTwo{prefix}DesignCount", row["n_designs"],
                   str(row["n_designs"]), "designs",
                   "Count designs in the frozen primary scope.", primary_source)
    for index, value in enumerate(primary["report"]["rf"]["per_seed"], 1):
        word = "One" if index == 1 else "Two"
        for scope, prefix in primary_prefixes.items():
            claims.add(f"StudyTwoRfSeed{word}{prefix}Gain", value[scope],
                       fmt(value[scope]), "MHz",
                       "Independent RF training seed's RF-minus-SFT penalized Fmax effect.",
                       primary_source)

    # Primary-arm endpoint rows used by the compact headline table.  These are
    # kept in this ledger so no value (including the single-seed control) is
    # transcribed into TeX by hand.
    for arm, label in (("mlp", "Mlp"), ("correctness", "CorrectnessOnly")):
        row = primary["report"][arm]["combined"]["all"]
        claims.add(f"StudyTwoOverall{label}SftGain", row["mean_diff"],
                   fmt(row["mean_diff"]), "MHz",
                   f"Preregistered paired {arm}-minus-SFT penalized equal-sample Fmax effect.",
                   primary_source)
        claims.add(f"StudyTwoOverall{label}SftCiLow", row["ci_lo"],
                   fmt(row["ci_lo"]), "MHz",
                   f"Preregistered paired-bootstrap lower bound for {arm} minus SFT.",
                   primary_source)
        claims.add(f"StudyTwoOverall{label}SftCiHigh", row["ci_hi"],
                   fmt(row["ci_hi"]), "MHz",
                   f"Preregistered paired-bootstrap upper bound for {arm} minus SFT.",
                   primary_source)

    correctness = primary["report"]["correctness"]["combined"]["all"]
    claims.add("StudyTwoOverallCorrectnessOnlyPenalized", correctness["arm_equal"],
               fmt(correctness["arm_equal"]), "MHz",
               "Mean per-design correctness-only equal-sample post-route Fmax; failures score zero.",
               primary_source)
    claims.add("StudyTwoCorrectnessOnlyCorrectness", 100.0 * correctness["arm_correct"],
               fmt(100.0 * correctness["arm_correct"]), "percent",
               "Oracle-correct share of sealed correctness-only samples.",
               primary_source)
    prereg_source = [span(PREREG_PATH)]
    for key, value, method in (
        ("StudyTwoCorrectnessTrainingSeeds", 1,
         "Preregistered number of correctness-only training seeds."),
        ("StudyTwoMlpTrainingSeeds", 2,
         "Preregistered number of original-MLP-reward training seeds."),
        ("StudyTwoRfTrainingSeeds", 2,
         "Preregistered number of repaired-RF-reward training seeds."),
    ):
        claims.add(key, value, str(value), "training seeds", method, prereg_source)

    prereg = read_json(PREREG_PATH)
    protocol = prereg["training_protocol"]
    evaluation = prereg["evaluation"]
    environment = prereg["environment"]
    reward_spec = prereg["reward"]
    protocol_claims = (
        ("StudyTwoTrainingUpdates", protocol["target_updates"],
         str(protocol["target_updates"]), "optimizer updates",
         "Frozen non-flat optimizer-update target shared by every training arm."),
        ("StudyTwoMidpointUpdate", protocol["checkpoints_at_updates"][0],
         str(protocol["checkpoints_at_updates"][0]), "optimizer updates",
         "Frozen midpoint checkpoint index."),
        ("StudyTwoGroupSize", protocol["group_size"],
         str(protocol["group_size"]), "samples/group",
         "Frozen group size shared by every policy-training arm."),
        ("StudyTwoTrainingTemperature", protocol["temperature"],
         fmt(protocol["temperature"]), "temperature",
         "Frozen sampling temperature during policy training."),
        ("StudyTwoTrainingMaxTokens", protocol["max_tokens"],
         str(protocol["max_tokens"]), "tokens",
         "Frozen maximum completion-token budget during policy training."),
        ("StudyTwoLearningRate", protocol["learning_rate"],
         "1e-5", "learning rate",
         "Frozen AdamW learning rate shared by every policy-training arm."),
        ("StudyTwoKlCoefficient", protocol["kl_coef"],
         fmt(protocol["kl_coef"]), "coefficient",
         "Frozen KL coefficient to the supervised adapter."),
        ("StudyTwoSamplesPerArmDesign", evaluation["samples_per_arm_per_design"],
         str(evaluation["samples_per_arm_per_design"]), "samples/arm/design",
         "Frozen endpoint sample budget for every arm and design."),
        ("StudyTwoSamplesPerSeedDesign", evaluation["samples_per_design_per_seed"],
         str(evaluation["samples_per_design_per_seed"]), "samples/seed/design",
         "Frozen endpoint sample budget for each seed in a two-seed arm."),
        ("StudyTwoMidSamplesPerSeedDesign", evaluation["mid_checkpoint_samples_per_design_per_seed"],
         str(evaluation["mid_checkpoint_samples_per_design_per_seed"]), "samples/seed/design",
         "Frozen midpoint sample budget for each repaired-RF seed and design."),
        ("StudyTwoEvaluationTemperature", evaluation["decoding"]["temperature"],
         fmt(evaluation["decoding"]["temperature"]), "temperature",
         "Frozen sampling temperature during sealed evaluation."),
        ("StudyTwoOracleStreams", len(evaluation["oracle_seeds"]),
         str(len(evaluation["oracle_seeds"])), "stimulus streams",
         "Count independent frozen oracle stimulus streams per candidate."),
        ("StudyTwoOracleVectors", evaluation["oracle_n"],
         f"{evaluation['oracle_n']:,}", "vectors/stream",
         "Frozen vector count in each oracle stimulus stream."),
        ("StudyTwoVivadoEnvironment", environment["vivado"],
         environment["vivado"], "tool and target",
         "Frozen Vivado version, execution host class, and FPGA target."),
        ("StudyTwoRewardFeatureCount", len(reward_spec["features"]),
         str(len(reward_spec["features"])), "canonical structural features",
         "Count frozen canonical structural features used by the repaired RF reward."),
        ("StudyTwoRewardTreeCount", reward_spec["hyperparameters"]["n_estimators"],
         str(reward_spec["hyperparameters"]["n_estimators"]), "trees",
         "Frozen number of estimators in the repaired random-forest reward."),
        ("StudyTwoRewardTrainingRows", reward_spec["training_rows"]["n_expected"],
         str(reward_spec["training_rows"]["n_expected"]), "measured RTL rows",
         "Frozen reward-model training-row count after exclusions."),
        ("StudyTwoCanonicalizerVersion", prereg["canonicaliser"]["version"],
         prereg["canonicaliser"]["version"], "version",
         "Frozen lexical canonicalizer version used by the repaired reward."),
    )
    for key, value, display, unit, method in protocol_claims:
        claims.add(key, value, display, unit, method, prereg_source)

    bootstrap = primary["bootstrap"]
    claims.add("StudyTwoBootstrapReplicates", bootstrap["n"],
               f"{bootstrap['n']:,}", "resamples",
               "Frozen paired stratified-bootstrap resample count.", primary_source)
    claims.add("StudyTwoBootstrapConfidence", 100.0 * bootstrap["ci"],
               fmt(100.0 * bootstrap["ci"], 0), "percent",
               "Frozen confidence level for the primary paired interval.", primary_source)

    diagnostics = primary["rf_group_diagnostics"]
    contract = primary["mutation_contract"]
    for key, value, display, unit, method in (
        ("StudyTwoEligibleGroups", diagnostics["eligible_groups"],
         str(diagnostics["eligible_groups"]), "training groups",
         "RF training groups containing at least two correct candidates with distinct canonical feature vectors."),
        ("StudyTwoResolvedGroups", diagnostics["resolved_groups"],
         str(diagnostics["resolved_groups"]), "training groups",
         "Eligible RF groups whose frozen predictor spans more than the preregistered resolution threshold."),
        ("StudyTwoRewardResolution", 100.0 * diagnostics["resolved_fraction"],
         fmt(100.0 * diagnostics["resolved_fraction"], 1), "percent",
         "Resolved eligible RF groups divided by all eligible RF groups."),
        ("StudyTwoContractCandidates", contract["n"], str(contract["n"]),
         "distinct candidates",
         "Reward-eligible distinct RF-training candidates audited by the frozen contract."),
        ("StudyTwoContractPassed", contract["passed"], str(contract["passed"]),
         "distinct candidates",
         "Reward-eligible distinct candidates passing canonical metadata, compilation, and sampled trace checks."),
        ("StudyTwoContractRejected", contract["rejected"], str(contract["rejected"]),
         "distinct candidates", "Reward-eligible distinct candidates rejected by the frozen contract."),
        ("StudyTwoContractCollisions", contract["collisions"], str(contract["collisions"]),
         "cross-design collisions", "Cross-design canonical collisions found by the frozen contract."),
    ):
        claims.add(key, value, display, unit, method, primary_source)

    study2_prereg = read_json(PREREG_STUDY2_PATH)
    trace_vectors = study2_prereg["study2"]["reward_eligible_gate"]["trace_vectors"]
    claims.add("StudyTwoContractTraceVectors", trace_vectors,
               str(trace_vectors), "vectors/seed",
               "Frozen sampled trace-equivalence vector count per oracle seed.",
               [span(PREREG_STUDY2_PATH)])
    late = primary["late_divergence"]["by_regime"]
    for scope, prefix in (("interp", "Interp"), ("extrap", "Extrap")):
        claims.add(f"StudyTwo{prefix}MidFmax", late[scope]["mid_equal_fmax"],
                   fmt(late[scope]["mid_equal_fmax"]), "MHz",
                   "Penalized equal-sample RF Fmax at the frozen midpoint checkpoint.",
                   primary_source)
        claims.add(f"StudyTwo{prefix}EndFmax", late[scope]["end_equal_fmax"],
                   fmt(late[scope]["end_equal_fmax"]), "MHz",
                   "Penalized equal-sample RF Fmax at the frozen endpoint checkpoint.",
                   primary_source)

    prefixes = {"interp": "Interp", "extrap": "Extrap", "all": "Overall"}
    for scope, prefix in prefixes.items():
        row = direct[scope]
        for arm, label in (("sft", "Sft"), ("mlp", "Mlp"), ("rf", "Rf")):
            claims.add(
                f"StudyTwo{prefix}{label}Penalized", row[f"{arm}_equal"],
                fmt(row[f"{arm}_equal"]), "MHz",
                "Mean per-design equal-sample post-route Fmax; incorrect and implementation-failed samples score zero.",
                direct_sources,
            )
        claims.add(f"StudyTwo{prefix}RfMlpGain", row["rf_minus_mlp"],
                   fmt(row["rf_minus_mlp"]), "MHz",
                   "Mean paired per-design RF-minus-MLP penalized equal-sample Fmax.",
                   direct_sources)
        claims.add(f"StudyTwo{prefix}RfMlpCiLow", row["ci_lo"], fmt(row["ci_lo"]), "MHz",
                   f"Family-by-regime stratified paired bootstrap lower bound; seed {BOOT_SEED}, {N_BOOT} resamples.",
                   direct_sources)
        claims.add(f"StudyTwo{prefix}RfMlpCiHigh", row["ci_hi"], fmt(row["ci_hi"]), "MHz",
                   f"Family-by-regime stratified paired bootstrap upper bound; seed {BOOT_SEED}, {N_BOOT} resamples.",
                   direct_sources)

    for arm, label in (("sft", "Sft"), ("mlp", "Mlp"), ("rf", "Rf")):
        claims.add(f"StudyTwo{label}Correctness", 100.0 * cov[arm]["correct_rate"],
                   fmt(100.0 * cov[arm]["correct_rate"]), "percent",
                   "Oracle-correct sample count divided by all generated samples across the sealed designs.",
                   arm_sources[arm])
        claims.add(f"StudyTwo{label}Synthesis", 100.0 * cov[arm]["synth_rate"],
                   fmt(100.0 * cov[arm]["synth_rate"]), "percent",
                   "Successfully implemented oracle-correct sample count divided by all generated samples.",
                   arm_sources[arm])

    claims.add("StudyTwoPpaCommonSupport", resources["n_common_support"],
               str(resources["n_common_support"]), "designs",
               "Designs with at least one compiled oracle-correct sample in SFT, RF, and MLP.",
               ppa_sources)
    metric_labels = {
        "lut": ("Lut", "LUTs", 1),
        "ff": ("Ff", "flip-flops", 1),
        "dsp": ("Dsp", "DSP blocks", 2),
        "bram": ("Bram", "BRAM blocks", 2),
        "power_w": ("Power", "W", 3),
    }
    for metric, (label, unit, digits) in metric_labels.items():
        row = resources["metrics"][metric]["all"]
        for arm, arm_label in (("sft", "Sft"), ("mlp", "Mlp"), ("rf", "Rf")):
            value = row["means"][arm]
            claims.add(f"StudyTwoPpa{arm_label}{label}", value, fmt(value, digits), unit,
                       "Equal-design mean of multiplicity-weighted conditional PPA on three-arm common support.",
                       ppa_sources)
        comparison = row["comparisons"]["rf_minus_sft"]
        claims.add(f"StudyTwoPpaRfSft{label}Diff", comparison["mean_diff"],
                   fmt(comparison["mean_diff"], digits), unit,
                   "Mean paired RF-minus-SFT conditional PPA difference on three-arm common support.",
                   ppa_sources)
        claims.add(f"StudyTwoPpaRfSft{label}CiLow", comparison["ci_lo"],
                   fmt(comparison["ci_lo"], digits), unit,
                   f"Paired stratified-bootstrap lower bound on conditional PPA difference; seed {BOOT_SEED}, {N_BOOT} resamples.",
                   ppa_sources)
        claims.add(f"StudyTwoPpaRfSft{label}CiHigh", comparison["ci_hi"],
                   fmt(comparison["ci_hi"], digits), unit,
                   f"Paired stratified-bootstrap upper bound on conditional PPA difference; seed {BOOT_SEED}, {N_BOOT} resamples.",
                   ppa_sources)

    for family_id, label in FAMILY_LABELS.items():
        row = family[family_id]
        source = reviewer_sources["family"]
        claims.add(f"StudyTwoFamily{label}Count", row["n_designs"],
                   str(row["n_designs"]), "designs",
                   "Reviewer-requested post-primary sealed family design count.", source)
        claims.add(f"StudyTwoFamily{label}InterpCount", row["n_interp"],
                   str(row["n_interp"]), "designs",
                   "Reviewer-requested post-primary interpolation count within family.", source)
        claims.add(f"StudyTwoFamily{label}ExtrapCount", row["n_extrap"],
                   str(row["n_extrap"]), "designs",
                   "Reviewer-requested post-primary extrapolation count within family.", source)
        for arm, arm_label in (("sft_equal", "Sft"), ("rf_equal", "Rf"),
                               ("rf_minus_sft", "Gain")):
            claims.add(f"StudyTwoFamily{label}{arm_label}", row[arm],
                       fmt(row[arm]), "MHz",
                       "Reviewer-requested descriptive family mean on the immutable sealed endpoint; no family-level interval.",
                       source)

    unstratified = sensitivity["unstratified_paired_bootstrap"]
    claims.add("StudyTwoSensitivityUnstratifiedCiLow", unstratified["ci_lo"],
               fmt(unstratified["ci_lo"]), "MHz",
               "Reviewer-requested unstratified paired percentile-bootstrap sensitivity lower bound.",
               reviewer_sources["sensitivity"])
    claims.add("StudyTwoSensitivityUnstratifiedCiHigh", unstratified["ci_hi"],
               fmt(unstratified["ci_hi"]), "MHz",
               "Reviewer-requested unstratified paired percentile-bootstrap sensitivity upper bound.",
               reviewer_sources["sensitivity"])
    leave_out = sensitivity["leave_one_family_out"]
    claims.add("StudyTwoSensitivityLeaveFamilyOutMin", leave_out["minimum"],
               fmt(leave_out["minimum"]), "MHz",
               "Minimum mean paired RF-minus-SFT effect across five leave-one-family-out omissions.",
               reviewer_sources["sensitivity"])
    claims.add("StudyTwoSensitivityLeaveFamilyOutMax", leave_out["maximum"],
               fmt(leave_out["maximum"]), "MHz",
               "Maximum mean paired RF-minus-SFT effect across five leave-one-family-out omissions.",
               reviewer_sources["sensitivity"])

    claims.add("StudyTwoSealedMechanismCommonCount",
               sealed_support["common_correct_support_designs"],
               str(sealed_support["common_correct_support_designs"]), "designs",
               "Sealed designs with at least one oracle-correct sampled string under both SFT and RF.",
               reviewer_sources["support"])
    claims.add("StudyTwoSealedMechanismSupportCount",
               sealed_support["sft_support_at_or_above_rf_conditional"],
               str(sealed_support["sft_support_at_or_above_rf_conditional"]), "designs",
               "Common-support designs where measured SFT support contains a candidate at least as fast as the RF conditional mean.",
               reviewer_sources["support"])
    claims.add("StudyTwoSealedMechanismSftEffective",
               sealed_support["sft_effective_support"],
               fmt(sealed_support["sft_effective_support"], 2), "effective strings",
               "Mean inverse-Simpson effective correct-string count on sealed SFT/RF common support.",
               reviewer_sources["support"])
    claims.add("StudyTwoSealedMechanismRfEffective",
               sealed_support["rf_effective_support"],
               fmt(sealed_support["rf_effective_support"], 2), "effective strings",
               "Mean inverse-Simpson effective correct-string count on sealed SFT/RF common support.",
               reviewer_sources["support"])

    claims.add("StudyTwoCaseDesign", rtl_case["design"],
               rtl_case["design"].replace("_", r"\_"),
               "design identifier", "Post-review illustrative sealed design identifier.",
               reviewer_sources["rtl_case"])
    for arm, label in (("sft", "Sft"), ("rf", "Rf")):
        row = rtl_case["arms"][arm]
        claims.add(f"StudyTwoCase{label}Module", row["module"],
                   row["module"].replace("_", r"\_"),
                   "candidate identifier", "Fixed illustrative dominant candidate identifier.",
                   reviewer_sources["rtl_case"])
        for field, field_label, unit, digits in (
            ("sample_mass", "Mass", "percent", 1),
            ("fmax", "Fmax", "MHz", 1),
            ("lut", "Lut", "LUTs", 0),
            ("ff", "Ff", "flip-flops", 0),
            ("dsp", "Dsp", "DSP blocks", 0),
        ):
            value = 100.0 * row[field] if field == "sample_mass" else row[field]
            claims.add(f"StudyTwoCase{label}{field_label}", value,
                       fmt(value, digits), unit,
                       "Post-review source-level illustrative candidate diagnostic; not a population estimate.",
                       reviewer_sources["rtl_case"])
    return claims


def tex_claims(claims: Claims) -> str:
    lines = [
        "% AUTO-GENERATED by analyze_study2_secondary.py. DO NOT EDIT.",
        "% Every value is backed by paper/generated/study2_claims.json.",
        r"\providecommand{\studyclaim}[1]{\csname StudyClaim#1\endcsname}",
        "",
    ]
    for key, row in claims.data.items():
        lines.append(f"% CLAIM {key}: {row['unit']}; {row['method']}")
        for source in row["sources"]:
            lines.append(f"% SOURCE {source}")
        display = row["display"].replace("%", r"\%")
        lines.append(rf"\expandafter\def\csname StudyClaim{key}\endcsname{{{display}}}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def provenance_markdown(claims: Claims) -> str:
    lines = [
        "# Study 2 secondary claim provenance",
        "",
        "Generated by `analyze_study2_secondary.py`; do not hand edit.",
        "",
        "| Claim | Display | Unit | Sources |",
        "|---|---:|---|---|",
    ]
    for key, row in claims.data.items():
        lines.append(
            f"| `{key}` | {row['display']} | {row['unit']} | "
            + "<br>".join(f"`{source}`" for source in row["sources"])
            + " |"
        )
    return "\n".join(lines) + "\n"


def table_comparison() -> str:
    return r"""% AUTO-GENERATED by analyze_study2_secondary.py. DO NOT EDIT.
\begin{table*}[t]
\centering
\caption{Sealed Study 2 endpoint comparison. All values are penalized
equal-sample post-route Fmax in MHz; failures score zero. RF--SFT intervals are
the frozen primary analysis; RF--MLP intervals are post-primary paired
stratified-bootstrap diagnostics.}
\label{tab:study2-comparison}
\small
\begin{tabular}{lrrrrr}
\toprule
Regime & SFT & MLP & RF & RF--SFT [CI] & RF--MLP [CI] \\
\midrule
Interpolation & \studyclaim{StudyTwoInterpSftPenalized} &
\studyclaim{StudyTwoInterpMlpPenalized} & \studyclaim{StudyTwoInterpRfPenalized} &
\studyclaim{StudyTwoInterpRfSftGain}
[\studyclaim{StudyTwoInterpRfSftCiLow}, \studyclaim{StudyTwoInterpRfSftCiHigh}] &
\studyclaim{StudyTwoInterpRfMlpGain}
[\studyclaim{StudyTwoInterpRfMlpCiLow}, \studyclaim{StudyTwoInterpRfMlpCiHigh}] \\
Extrapolation & \studyclaim{StudyTwoExtrapSftPenalized} &
\studyclaim{StudyTwoExtrapMlpPenalized} & \studyclaim{StudyTwoExtrapRfPenalized} &
\studyclaim{StudyTwoExtrapRfSftGain}
[\studyclaim{StudyTwoExtrapRfSftCiLow}, \studyclaim{StudyTwoExtrapRfSftCiHigh}] &
\studyclaim{StudyTwoExtrapRfMlpGain}
[\studyclaim{StudyTwoExtrapRfMlpCiLow}, \studyclaim{StudyTwoExtrapRfMlpCiHigh}] \\
Overall & \studyclaim{StudyTwoOverallSftPenalized} &
\studyclaim{StudyTwoOverallMlpPenalized} & \studyclaim{StudyTwoOverallRfPenalized} &
\studyclaim{StudyTwoOverallRfSftGain}
[\studyclaim{StudyTwoOverallRfSftCiLow}, \studyclaim{StudyTwoOverallRfSftCiHigh}] &
\studyclaim{StudyTwoOverallRfMlpGain}
[\studyclaim{StudyTwoOverallRfMlpCiLow}, \studyclaim{StudyTwoOverallRfMlpCiHigh}] \\
\bottomrule
\end{tabular}
\end{table*}
"""


def table_primary() -> str:
    return r"""% AUTO-GENERATED by analyze_study2_secondary.py. DO NOT EDIT.
\begin{table*}[t]
\centering
\caption{Headline sealed Study 2 comparison over the same
\studyclaim{StudyTwoDesignCount} designs. Penalized
Fmax is averaged equally over designs and scores incorrect or implementation-
failed samples as zero. Confidence intervals are paired, stratified 95\%
bootstrap intervals versus the SFT baseline.}
\label{tab:study2-primary}
\small
\begin{tabular}{lrrrr}
\toprule
Arm & Training seeds & Penalized Fmax [MHz] & Correct [\%] & $\Delta$ vs. SFT [95\% CI] \\
\midrule
SFT & -- & \studyclaim{StudyTwoOverallSftPenalized} &
\studyclaim{StudyTwoSftCorrectness} & -- \\
Correctness only & \studyclaim{StudyTwoCorrectnessTrainingSeeds} &
\studyclaim{StudyTwoOverallCorrectnessOnlyPenalized} &
\studyclaim{StudyTwoCorrectnessOnlyCorrectness} &
\studyclaim{StudyTwoOverallCorrectnessOnlySftGain}
[\studyclaim{StudyTwoOverallCorrectnessOnlySftCiLow},
 \studyclaim{StudyTwoOverallCorrectnessOnlySftCiHigh}] \\
Original MLP reward & \studyclaim{StudyTwoMlpTrainingSeeds} &
\studyclaim{StudyTwoOverallMlpPenalized} & \studyclaim{StudyTwoMlpCorrectness} &
\studyclaim{StudyTwoOverallMlpSftGain}
[\studyclaim{StudyTwoOverallMlpSftCiLow},
 \studyclaim{StudyTwoOverallMlpSftCiHigh}] \\
Repaired RF reward & \studyclaim{StudyTwoRfTrainingSeeds} &
\studyclaim{StudyTwoOverallRfPenalized} & \studyclaim{StudyTwoRfCorrectness} &
\studyclaim{StudyTwoOverallRfSftGain}
[\studyclaim{StudyTwoOverallRfSftCiLow},
 \studyclaim{StudyTwoOverallRfSftCiHigh}] \\
\bottomrule
\end{tabular}
\end{table*}
"""


def table_rf_replication() -> str:
    return r"""% AUTO-GENERATED by analyze_study2_secondary.py. DO NOT EDIT.
\begin{table*}[t]
\centering
\caption{Independent repaired-RF training-seed effects on the sealed endpoint.
Seed rows are separately reported point estimates; the seed-averaged row uses
the frozen paired, stratified 95\% bootstrap intervals.}
\label{tab:study2-rf-seeds}
\small
\begin{tabular}{lrrr}
\toprule
Estimate & Interpolation & Extrapolation & Overall \\
\midrule
RF seed 1 & \studyclaim{StudyTwoRfSeedOneInterpGain} &
\studyclaim{StudyTwoRfSeedOneExtrapGain} &
\studyclaim{StudyTwoRfSeedOneOverallGain} \\
RF seed 2 & \studyclaim{StudyTwoRfSeedTwoInterpGain} &
\studyclaim{StudyTwoRfSeedTwoExtrapGain} &
\studyclaim{StudyTwoRfSeedTwoOverallGain} \\
Seed average [95\% CI] &
\studyclaim{StudyTwoInterpRfSftGain}
[\studyclaim{StudyTwoInterpRfSftCiLow}, \studyclaim{StudyTwoInterpRfSftCiHigh}] &
\studyclaim{StudyTwoExtrapRfSftGain}
[\studyclaim{StudyTwoExtrapRfSftCiLow}, \studyclaim{StudyTwoExtrapRfSftCiHigh}] &
\studyclaim{StudyTwoOverallRfSftGain}
[\studyclaim{StudyTwoOverallRfSftCiLow}, \studyclaim{StudyTwoOverallRfSftCiHigh}] \\
\bottomrule
\end{tabular}
\end{table*}
"""


def table_family() -> str:
    rows = []
    for family_id, (label, display) in zip(
        FAMILY_LABELS,
        (("Fir", "FIR"), ("ReverseFir", "Reverse FIR"),
         ("Polynomial", "Polynomial"), ("Recursive", "Recursive filter"),
         ("Median", "Median filter")),
    ):
        del family_id
        rows.append(
            f"{display} & \\studyclaim{{StudyTwoFamily{label}Count}} & "
            f"\\studyclaim{{StudyTwoFamily{label}InterpCount}}/"
            f"\\studyclaim{{StudyTwoFamily{label}ExtrapCount}} & "
            f"\\studyclaim{{StudyTwoFamily{label}Sft}} & "
            f"\\studyclaim{{StudyTwoFamily{label}Rf}} & "
            f"\\studyclaim{{StudyTwoFamily{label}Gain}} \\\\"
        )
    return r"""% AUTO-GENERATED by analyze_study2_secondary.py. DO NOT EDIT.
\begin{table*}[t]
\centering
\caption{Post-primary descriptive family breakdown of the sealed
failure-penalized endpoint. I/E gives interpolation/extrapolation design counts.
Rows are descriptive point estimates; the small and unequal family cells do not
support stable family-level confidence intervals.}
\label{tab:study2-family}
\small
\begin{tabular}{lrrrrr}
\toprule
Family & Designs & I/E & SFT [MHz] & RF [MHz] & RF--SFT [MHz] \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table*}
"""


def table_rtl_case() -> str:
    return r"""% AUTO-GENERATED by analyze_study2_secondary.py. DO NOT EDIT.
\begin{table*}[t]
\centering
\caption{Illustrative source-level contrast for
\studyclaim{StudyTwoCaseDesign}. The entries are the dominant SFT candidate and
dominant candidate from RF seed one for that design. Selection occurred after
manuscript assessment; this example explains a possible CAD mechanism but is not a
population or causal estimate.}
\label{tab:study2-rtl-case}
\small
\begin{tabularx}{\textwidth}{lXrrrrr}
\toprule
Arm & Observed RTL organization & Sample mass [\%] & Fmax [MHz] & LUT & FF & DSP \\
\midrule
SFT & Delayed samples and product registers followed by a parallel final sum &
\studyclaim{StudyTwoCaseSftMass} & \studyclaim{StudyTwoCaseSftFmax} &
\studyclaim{StudyTwoCaseSftLut} & \studyclaim{StudyTwoCaseSftFf} &
\studyclaim{StudyTwoCaseSftDsp} \\
RF seed one & Registered transposed multiply--accumulate chain &
\studyclaim{StudyTwoCaseRfMass} & \studyclaim{StudyTwoCaseRfFmax} &
\studyclaim{StudyTwoCaseRfLut} & \studyclaim{StudyTwoCaseRfFf} &
\studyclaim{StudyTwoCaseRfDsp} \\
\bottomrule
\end{tabularx}
\end{table*}
"""


def table_ppa() -> str:
    rows = []
    for label, claim, unit in (
        ("LUTs", "Lut", ""),
        ("Flip-flops", "Ff", ""),
        ("DSP blocks", "Dsp", ""),
        ("BRAM blocks", "Bram", ""),
        ("Vectorless power", "Power", "W"),
    ):
        metric = f"{label} [{unit}]" if unit else label
        rows.append(
            f"{metric} & \\studyclaim{{StudyTwoPpaSft{claim}}} & "
            f"\\studyclaim{{StudyTwoPpaMlp{claim}}} & "
            f"\\studyclaim{{StudyTwoPpaRf{claim}}} & "
            f"\\studyclaim{{StudyTwoPpaRfSft{claim}Diff}} "
            f"[\\studyclaim{{StudyTwoPpaRfSft{claim}CiLow}}, "
            f"\\studyclaim{{StudyTwoPpaRfSft{claim}CiHigh}}] \\\\"
        )
    body = "\n".join(rows)
    return rf"""% AUTO-GENERATED by analyze_study2_secondary.py. DO NOT EDIT.
\begin{{table*}}[t]
\centering
\caption{{Conditional physical-cost diagnostics on the
\studyclaim{{StudyTwoPpaCommonSupport}}-design three-arm common support. Values
are multiplicity-weighted within design and equally weighted across designs.
Power is Vivado's vectorless estimate, not board power.}}
\label{{tab:study2-ppa}}
\small
\begin{{tabular}}{{lrrrr}}
\toprule
Metric & SFT & MLP & RF & RF--SFT difference [CI] \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table*}}
"""


def render() -> tuple[dict[pathlib.Path, str], dict]:
    spec = read_json(SPEC_PATH)
    verify_frozen_inputs(spec)
    primary = read_json(PRIMARY_RESULT_PATH)
    if primary.get("outcome") != spec["immutable_primary_outcome"]:
        raise SecondaryAnalysisError("primary result outcome differs from frozen specification")
    ppa = verify_ppa_audit(read_json(PPA_AUDIT_PATH))
    validate_configs()
    _, designs, meta = load_sealed(str(SEALED_PATH))
    if len(designs) != spec["invariants"]["designs"]:
        raise SecondaryAnalysisError("sealed design count differs from secondary specification")
    arms, arm_sources = load_arms(designs, meta, primary)
    direct = direct_comparison(arms, designs, meta, primary)
    resources = resource_summary(arms, designs, meta)
    cov = coverage(arms, designs)
    family = reviewer_family_breakdown(arms, designs, meta)
    sensitivity = reviewer_sensitivity(arms, designs, meta, spec)
    sealed_support, support_sources = reviewer_sealed_support(designs)
    rtl_case, rtl_case_sources = reviewer_rtl_case(spec)
    reviewer_sources = {
        "family": sorted(set(arm_sources["sft"] + arm_sources["rf"] + [span(SEALED_PATH), span(SPEC_PATH)])),
        "sensitivity": sorted(set(arm_sources["sft"] + arm_sources["rf"] + [span(SEALED_PATH), span(SPEC_PATH)])),
        "support": sorted(set(support_sources + [span(SPEC_PATH)])),
        "rtl_case": rtl_case_sources,
    }
    claims = build_claims(
        primary, direct, resources, cov, ppa, arm_sources,
        family, sensitivity, sealed_support, rtl_case, reviewer_sources,
    )
    result = {
        "schema": "study2_secondary_results/2",
        "status": spec["status"],
        "reviewer_revision": spec["reviewer_revision"],
        "primary_outcome_unchanged": primary["outcome"],
        "spec_sha256_lf": sha256_lf(SPEC_PATH),
        "input_sha256_lf": spec["inputs_sha256_lf"],
        "ppa_audit": ppa,
        "coverage": cov,
        "direct_rf_mlp": direct,
        "resource_power": resources,
        "reviewer_requested": {
            "family_breakdown": family,
            "sensitivity": sensitivity,
            "sealed_support": sealed_support,
            "illustrative_rtl_case": rtl_case,
        },
        "reporting_rules": spec["reporting_rules"],
    }
    ledger = {
        "schema": 1,
        "generator": "analyze_study2_secondary.py",
        "claims": claims.data,
    }
    outputs = {
        OUTPUT_PATH: json.dumps(result, indent=2) + "\n",
        GENERATED / "study2_claims.json": json.dumps(ledger, indent=2) + "\n",
        GENERATED / "study2_claims.tex": tex_claims(claims),
        GENERATED / "study2_claim_provenance.md": provenance_markdown(claims),
        GENERATED / "study2_table_primary.tex": table_primary(),
        GENERATED / "study2_table_rf_replication.tex": table_rf_replication(),
        GENERATED / "study2_table_comparison.tex": table_comparison(),
        GENERATED / "study2_table_ppa.tex": table_ppa(),
        GENERATED / "study2_table_family.tex": table_family(),
        GENERATED / "study2_table_rtl_case.tex": table_rtl_case(),
    }
    return outputs, result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated outputs are stale")
    args = parser.parse_args()
    outputs, result = render()
    if args.check:
        stale = [
            rel(path) for path, content in outputs.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            print("STALE Study 2 secondary artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {path}", file=sys.stderr)
            return 1
        print("OK: Study 2 secondary artifacts are current and provenance-complete")
        return 0
    GENERATED.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote {rel(path)}")
    for scope in SCOPES:
        row = result["direct_rf_mlp"][scope]
        print(
            f"{scope:7s}: RF {row['rf_equal']:.1f} - MLP {row['mlp_equal']:.1f} "
            f"= {row['rf_minus_mlp']:+.1f} "
            f"[{row['ci_lo']:+.1f}, {row['ci_hi']:+.1f}] MHz"
        )
    print(
        "resource common support:",
        result["resource_power"]["n_common_support"],
        "/", result["direct_rf_mlp"]["all"]["n_designs"], "designs",
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SecondaryAnalysisError, ValueError) as exc:
        raise SystemExit(f"Study 2 secondary analysis error: {exc}")
