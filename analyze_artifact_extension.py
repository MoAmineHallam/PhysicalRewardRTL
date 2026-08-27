#!/usr/bin/env python3
"""Generate a bounded, artifact-only extension to sealed Study 2.

This script does not train a model, generate RTL, invoke an oracle, run Vivado,
or alter the completed Study 2 result.  It reconstructs three reviewer-facing
diagnostics exclusively from committed sealed artifacts:

1. the exact F = q * mu decomposition, where q is the oracle-correct draw
   probability and mu is mean post-route Fmax conditional on oracle correctness
   (an implementation failure remains 0 MHz);
2. a deterministic lexical-structure comparison of SFT, repaired-RF, and
   correctness-only correct endpoint RTL, plus one mechanically selected case;
3. the empirical perfect-selector SFT best-of-N curve on sealed Study 2 and
   separate accounting for LLM draws, oracle work, raw correct implementations,
   and content-deduplicated correct implementations.

The analysis is deliberately post-primary and descriptive.  It must never be
presented as a preregistered outcome, a new independent test set, or evidence
that the single-constraint WNS-derived Fmax proxy equals true timing closure.

Usage:
    python analyze_artifact_extension.py
    python analyze_artifact_extension.py --check
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import pathlib
import statistics
import sys
from collections import Counter, OrderedDict, defaultdict
from typing import Any, Iterable, Mapping, Sequence

from canonicalize import STRUCT_FEATURES, canonicalize, struct_feature_dict


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_PATH = ROOT / "artifact_extension_results.json"
PROVENANCE_PATH = ROOT / "artifact_extension_provenance.md"

SEALED_SPLIT = ROOT / "sealed_split.json"
SEALED_RESULTS = ROOT / "sealed_results_study2.json"
PPA_AUDIT = ROOT / "sealed_ppa_audit_study2.json"
CANONICALIZER = ROOT / "canonicalize.py"

ARM_DIRS: "OrderedDict[str, tuple[pathlib.Path, ...]]" = OrderedDict([
    ("sft", (ROOT / "rtl" / "sealed_sft",)),
    ("rf", (ROOT / "rtl" / "sealed_rf_s1",
            ROOT / "rtl" / "sealed_rf_s2")),
    ("mlp", (ROOT / "rtl" / "sealed_mlp_s1",
             ROOT / "rtl" / "sealed_mlp_s2")),
    ("correctness", (ROOT / "rtl" / "sealed_corr_s1",)),
])

STRUCTURAL_ARMS = ("sft", "rf", "correctness")
EXPECTED_DRAWS_PER_DESIGN = 48
BEST_OF_NS = tuple(range(1, 49))
FLOAT_TOL = 1e-10


class ArtifactExtensionError(RuntimeError):
    """An input or generated output violates the extension contract."""


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256_lf(path: pathlib.Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def line_count(path: pathlib.Path) -> int:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return len(raw.splitlines())


def span(path: pathlib.Path) -> str:
    return f"{rel(path)}:1-{line_count(path)}"


def read_json(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ArtifactExtensionError(f"cannot read JSON {rel(path)}: {exc}") from exc


def close(a: float, b: float, tol: float = FLOAT_TOL) -> bool:
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ArtifactExtensionError(message)


def finite_nonnegative(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ArtifactExtensionError(f"{label} is not numeric: {value!r}") from exc
    require(math.isfinite(number) and number >= 0.0,
            f"{label} must be finite and nonnegative, got {number!r}")
    return number


def combined_digest(members: Iterable[tuple[str, str]]) -> str:
    digest = hashlib.sha256()
    for path, file_hash in sorted(members):
        digest.update(path.encode("utf-8") + b"\0" +
                      file_hash.encode("ascii") + b"\n")
    return digest.hexdigest()


@dataclasses.dataclass(frozen=True)
class DesignMeta:
    design: str
    family: str
    regime: str
    max_tokens: int


@dataclasses.dataclass
class Candidate:
    arm: str
    policy: str
    directory: pathlib.Path
    module: str
    design: str
    count: int
    n: int
    content_key: str
    rtl_path: pathlib.Path
    manifest_source: str
    ppa_source: str
    fmax_mhz: float
    implemented: bool
    features: dict[str, float] | None = None


@dataclasses.dataclass
class DirectoryEvidence:
    path: pathlib.Path
    policy: str
    n_per_design: int
    oracle_streams: int
    candidates: list[Candidate]
    correct_by_design: dict[str, int]
    draws_by_design: dict[str, int]
    input_paths: list[pathlib.Path]
    n_implementation_failures: int


@dataclasses.dataclass
class ArmEvidence:
    name: str
    directories: list[DirectoryEvidence]
    candidates: list[Candidate]
    draws_by_design: dict[str, int]
    correct_by_design: dict[str, int]


def load_split() -> "OrderedDict[str, DesignMeta]":
    payload = read_json(SEALED_SPLIT)
    require(payload.get("schema") == "sealed_split/1",
            "sealed split schema changed")
    rows = payload.get("designs")
    require(isinstance(rows, list) and len(rows) == payload.get("n_designs"),
            "sealed split design count is inconsistent")
    out: "OrderedDict[str, DesignMeta]" = OrderedDict()
    for row in rows:
        design = str(row.get("design", ""))
        require(design and design not in out,
                f"missing or duplicate sealed design {design!r}")
        regime = str(row.get("regime", ""))
        require(regime in ("interp", "extrap"),
                f"invalid regime for {design}: {regime!r}")
        out[design] = DesignMeta(
            design=design,
            family=str(row.get("family", "")),
            regime=regime,
            max_tokens=int(row.get("max_tokens", 0)),
        )
        require(out[design].family != "" and out[design].max_tokens > 0,
                f"incomplete metadata for {design}")
    require(len(out) == 20, f"expected 20 sealed designs, found {len(out)}")
    return out


def parse_ppa(path: pathlib.Path) -> tuple[dict[str, tuple[dict, int]], list[pathlib.Path]]:
    rows: dict[str, tuple[dict, int]] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except ValueError as exc:
            raise ArtifactExtensionError(
                f"invalid JSON at {rel(path)}:{lineno}: {exc}") from exc
        module = str(row.get("module", ""))
        require(module and module not in rows,
                f"missing or duplicate PPA module at {rel(path)}:{lineno}")
        compiled = bool(row.get("compiled"))
        if compiled:
            finite_nonnegative(row.get("fmax_mhz"),
                               f"{rel(path)}:{lineno} fmax_mhz")
        else:
            require("fmax_mhz" not in row,
                    f"failed implementation has an Fmax at {rel(path)}:{lineno}")
        rows[module] = (row, lineno)
    return rows, [path]


def parse_failures(path: pathlib.Path) -> tuple[dict[str, int], list[pathlib.Path]]:
    failures: dict[str, int] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        module = raw.strip()
        if not module:
            continue
        require(module not in failures,
                f"duplicate implementation failure {module} in {rel(path)}")
        failures[module] = lineno
    return failures, [path]


def load_directory(
        arm: str, directory: pathlib.Path,
        designs: Mapping[str, DesignMeta], sealed_split_sha: str) -> DirectoryEvidence:
    require(directory.is_dir(), f"missing evidence directory {rel(directory)}")
    config_path = directory / "generation_config.json"
    manifest_path = directory / "fmax_manifest.json"
    summary_path = directory / "holdout_summary.json"
    ppa_path = directory / "ppa.jsonl"
    failures_path = directory / "ppa.jsonl.fails"
    for path in (config_path, manifest_path, summary_path, ppa_path, failures_path):
        require(path.is_file(), f"missing evidence file {rel(path)}")

    config = read_json(config_path)
    manifest = read_json(manifest_path)
    summary_payload = read_json(summary_path)
    require(config.get("schema") == "sealed_evaluation/1",
            f"unexpected config schema in {rel(config_path)}")
    policy = str(config.get("policy", ""))
    require(list(summary_payload) == [policy],
            f"summary policy mismatch in {rel(summary_path)}")
    summary = summary_payload[policy]
    require(set(summary) == set(designs),
            f"summary design universe mismatch in {rel(summary_path)}")
    n_per_design = int(config.get("n_per_design", 0))
    require(n_per_design > 0, f"invalid n_per_design in {rel(config_path)}")
    require(config.get("sealed_split_sha256") == sealed_split_sha,
            f"sealed split hash mismatch in {rel(config_path)}")
    oracle_seeds = config.get("oracle_seeds")
    require(isinstance(oracle_seeds, list) and oracle_seeds == [1, 2],
            f"oracle streams changed in {rel(config_path)}")

    ppa_rows, ppa_sources = parse_ppa(ppa_path)
    failures, failure_sources = parse_failures(failures_path)
    failed_ppa = {module for module, (row, _lineno) in ppa_rows.items()
                  if not bool(row.get("compiled"))}
    require(failed_ppa == set(failures),
            f".fails ledger disagrees with failed PPA rows in {rel(directory)}")
    require(set(ppa_rows) == set(manifest),
            f"PPA accounting does not cover the manifest in {rel(directory)}")

    correct_by_design: dict[str, int] = {design: 0 for design in designs}
    draws_by_design: dict[str, int] = {}
    candidates: list[Candidate] = []
    input_paths = [config_path, manifest_path, summary_path,
                   ppa_path, failures_path]

    for design, row in summary.items():
        n = int(row.get("n", -1))
        require(n == n_per_design,
                f"draw count mismatch for {design} in {rel(summary_path)}")
        draws_by_design[design] = n

    manifest_lines = manifest_path.read_text(encoding="utf-8").splitlines()
    module_line: dict[str, int] = {}
    for lineno, raw in enumerate(manifest_lines, 1):
        stripped = raw.strip()
        if stripped.startswith('"') and '": {' in stripped:
            key = stripped.split('"', 2)[1]
            if key in manifest:
                module_line[key] = lineno

    for module, info in manifest.items():
        require(info.get("policy") == policy,
                f"policy mismatch for {module} in {rel(manifest_path)}")
        design = str(info.get("design", ""))
        require(design in designs, f"unknown design {design!r} for {module}")
        count = int(info.get("count", 0))
        require(count > 0 and int(info.get("n", -1)) == n_per_design,
                f"invalid multiplicity for {module}")
        rtl_path = directory / f"{module}.sv"
        require(rtl_path.is_file(), f"missing emitted RTL {rel(rtl_path)}")
        emitted_hash = sha256_lf(rtl_path)
        require(emitted_hash == info.get("emitted_sha256"),
                f"emitted RTL hash mismatch for {rel(rtl_path)}")
        content_key = str(info.get("source_sha256", ""))
        require(len(content_key) == 64,
                f"missing full source content hash for {module}")
        correct_by_design[design] += count
        input_paths.append(rtl_path)
        ppa, ppa_lineno = ppa_rows[module]
        if bool(ppa.get("compiled")):
            fmax = finite_nonnegative(ppa["fmax_mhz"], f"PPA for {module}")
            ppa_source = f"{rel(ppa_path)}:{ppa_lineno}"
            implemented = True
        else:
            fmax = 0.0
            ppa_source = (f"{rel(ppa_path)}:{ppa_lineno}; "
                          f"{rel(failures_path)}:{failures[module]}")
            implemented = False
        candidates.append(Candidate(
            arm=arm,
            policy=policy,
            directory=directory,
            module=module,
            design=design,
            count=count,
            n=n_per_design,
            content_key=content_key,
            rtl_path=rtl_path,
            manifest_source=f"{rel(manifest_path)}:{module_line.get(module, 1)}",
            ppa_source=ppa_source,
            fmax_mhz=fmax,
            implemented=implemented,
        ))

    for design, row in summary.items():
        expected_correct = int(row.get("n_correct", -1))
        require(correct_by_design[design] == expected_correct,
                f"correct-draw multiplicity mismatch for {policy}/{design}")
        require(0 <= expected_correct <= n_per_design,
                f"invalid correctness count for {policy}/{design}")

    return DirectoryEvidence(
        path=directory,
        policy=policy,
        n_per_design=n_per_design,
        oracle_streams=len(oracle_seeds),
        candidates=candidates,
        correct_by_design=correct_by_design,
        draws_by_design=draws_by_design,
        input_paths=sorted(set(input_paths)),
        n_implementation_failures=len(failures),
    )


def audit_name(row: Mapping[str, Any]) -> str:
    return str(row.get("directory", "")).replace("\\", "/").rstrip("/").split("/")[-1]


def validate_ppa_audit(directories: Iterable[DirectoryEvidence]) -> None:
    audit = read_json(PPA_AUDIT)
    require(audit.get("schema") == "sealed_ppa_audit/1" and
            audit.get("complete") is True,
            "sealed PPA audit is not complete")
    audit_rows = {audit_name(row): row for row in audit.get("directories", [])}
    for evidence in directories:
        name = evidence.path.name
        require(name in audit_rows, f"{name} missing from sealed PPA audit")
        row = audit_rows[name]
        manifest_path = evidence.path / "fmax_manifest.json"
        ppa_path = evidence.path / "ppa.jsonl"
        require(row.get("manifest_sha256") == sha256_lf(manifest_path),
                f"PPA audit manifest hash mismatch for {name}")
        require(row.get("ppa_sha256") == sha256_lf(ppa_path),
                f"PPA audit row hash mismatch for {name}")
        require(int(row.get("n_candidates", -1)) == len(evidence.candidates),
                f"PPA audit candidate count mismatch for {name}")
        require(int(row.get("n_failed", -1)) == evidence.n_implementation_failures,
                f"PPA audit failure count mismatch for {name}")


def combine_arms(designs: Mapping[str, DesignMeta]) -> "OrderedDict[str, ArmEvidence]":
    sealed_sha = sha256_lf(SEALED_SPLIT)
    arms: "OrderedDict[str, ArmEvidence]" = OrderedDict()
    all_directories: list[DirectoryEvidence] = []
    for arm, paths in ARM_DIRS.items():
        directories = [load_directory(arm, path, designs, sealed_sha)
                       for path in paths]
        all_directories.extend(directories)
        candidates = [candidate for directory in directories
                      for candidate in directory.candidates]
        draws = {design: sum(directory.draws_by_design[design]
                             for directory in directories)
                 for design in designs}
        correct = {design: sum(directory.correct_by_design[design]
                               for directory in directories)
                   for design in designs}
        require(all(n == EXPECTED_DRAWS_PER_DESIGN for n in draws.values()),
                f"{arm} is not a 48-draw/design endpoint distribution")
        arms[arm] = ArmEvidence(arm, directories, candidates, draws, correct)
    validate_ppa_audit(all_directories)
    return arms


def candidates_by_design(arm: ArmEvidence) -> dict[str, list[Candidate]]:
    out: dict[str, list[Candidate]] = defaultdict(list)
    for candidate in arm.candidates:
        out[candidate.design].append(candidate)
    return out


def design_metrics(arm: ArmEvidence, design: str) -> dict[str, float | int]:
    rows = [candidate for candidate in arm.candidates
            if candidate.design == design]
    draws = arm.draws_by_design[design]
    correct = arm.correct_by_design[design]
    numerator = sum(candidate.count * candidate.fmax_mhz for candidate in rows)
    q = correct / draws
    penalized = numerator / draws
    mu = numerator / correct if correct else 0.0
    return {
        "n_draws": draws,
        "n_correct": correct,
        "q_correct": q,
        "mu_fmax_given_correct_mhz": mu,
        "penalized_fmax_mhz": penalized,
        "identity_residual_mhz": penalized - q * mu,
        "n_distinct_correct": len(rows),
        "n_distinct_implementation_failed": sum(not row.implemented for row in rows),
        "n_correct_draws_implementation_failed": sum(
            row.count for row in rows if not row.implemented),
    }


def scope_designs(
        designs: Mapping[str, DesignMeta], scope: str) -> list[str]:
    require(scope in ("all", "interp", "extrap"), f"invalid scope {scope}")
    return [design for design, meta in designs.items()
            if scope == "all" or meta.regime == scope]


def aggregate_decomposition(
        arm: ArmEvidence, selected_designs: Sequence[str]) -> dict[str, Any]:
    metrics = [design_metrics(arm, design) for design in selected_designs]
    draws = sum(int(row["n_draws"]) for row in metrics)
    correct = sum(int(row["n_correct"]) for row in metrics)
    numerator = sum(float(row["penalized_fmax_mhz"]) *
                    int(row["n_draws"]) for row in metrics)
    q = correct / draws
    penalized = numerator / draws
    mu = numerator / correct if correct else 0.0
    result = {
        "n_designs": len(selected_designs),
        "n_draws": draws,
        "n_correct": correct,
        "q_correct": q,
        "mu_fmax_given_correct_mhz": mu,
        "penalized_fmax_mhz": penalized,
        "identity_residual_mhz": penalized - q * mu,
        "n_distinct_correct": sum(int(row["n_distinct_correct"])
                                  for row in metrics),
        "n_distinct_implementation_failed": sum(
            int(row["n_distinct_implementation_failed"]) for row in metrics),
        "n_correct_draws_implementation_failed": sum(
            int(row["n_correct_draws_implementation_failed"]) for row in metrics),
    }
    require(abs(result["identity_residual_mhz"]) < 1e-12,
            f"F=q*mu identity failed for {arm.name}")
    return result


def validate_against_sealed_results(
        arms: Mapping[str, ArmEvidence], designs: Mapping[str, DesignMeta]) -> None:
    original = read_json(SEALED_RESULTS)
    require(original.get("designs") == list(designs),
            "sealed result design order changed")
    for arm_name, arm in arms.items():
        stored = original["sft"] if arm_name == "sft" else original["arms"][arm_name]
        for design in designs:
            got = design_metrics(arm, design)
            expected = stored[design]
            comparisons = [
                ("penalized_fmax_mhz", "equal"),
                ("q_correct", "correct_rate"),
            ]
            # The frozen analyzer seed-averages per-seed conditional means,
            # assigning 0 to a seed with no correct draws.  That quantity is
            # intentionally not the pooled mu required by F=q*mu.  They are
            # identical for the one-directory SFT/correctness arms only.
            if len(arm.directories) == 1:
                comparisons.append(
                    ("mu_fmax_given_correct_mhz", "cond_correct"))
            for got_key, expected_key in comparisons:
                require(close(got[got_key], expected[expected_key]),
                        f"reconstruction mismatch for {arm_name}/{design}/{got_key}")


def decomposition_section(
        arms: Mapping[str, ArmEvidence],
        designs: Mapping[str, DesignMeta]) -> dict[str, Any]:
    section: dict[str, Any] = {
        "definition": {
            "q": "oracle-correct draws divided by all draws",
            "mu": ("pooled correct-draw mean WNS-derived post-route Fmax over "
                   "the combined arm; unlike a mean of per-seed conditional means, "
                   "a correct RTL whose Vivado implementation failed contributes 0 MHz"),
            "F": "mean penalized Fmax over all draws, with every non-correct or implementation-failed draw at 0 MHz",
            "identity": "F = q * mu",
            "weighting": "equal draws per design and 48 draws per combined arm endpoint",
        },
        "arms": OrderedDict(),
    }
    for arm_name, arm in arms.items():
        per_design = OrderedDict(
            (design, design_metrics(arm, design)) for design in designs)
        section["arms"][arm_name] = {
            "all": aggregate_decomposition(arm, list(designs)),
            "interp": aggregate_decomposition(
                arm, scope_designs(designs, "interp")),
            "extrap": aggregate_decomposition(
                arm, scope_designs(designs, "extrap")),
            "per_design": per_design,
        }
    return section


def add_structural_features(arms: Mapping[str, ArmEvidence]) -> None:
    for arm_name in STRUCTURAL_ARMS:
        for candidate in arms[arm_name].candidates:
            source = candidate.rtl_path.read_text(encoding="utf-8")
            canonical, backend = canonicalize(source, "lexical")
            require(backend == "lexical",
                    f"unexpected canonicalization backend for {rel(candidate.rtl_path)}")
            features = struct_feature_dict(canonical)
            require(set(features) == set(STRUCT_FEATURES),
                    f"feature schema changed for {rel(candidate.rtl_path)}")
            candidate.features = {key: float(features[key])
                                  for key in STRUCT_FEATURES}


def weighted_feature(candidate_rows: Sequence[Candidate], feature: str) -> float:
    denominator = sum(row.count for row in candidate_rows)
    require(denominator > 0, "structural feature requested on empty support")
    return sum(row.count * float(row.features[feature])
               for row in candidate_rows) / denominator


def conditional_fmax(candidate_rows: Sequence[Candidate]) -> float:
    denominator = sum(row.count for row in candidate_rows)
    require(denominator > 0, "conditional Fmax requested on empty support")
    return sum(row.count * row.fmax_mhz for row in candidate_rows) / denominator


def representative_candidate(rows: Sequence[Candidate]) -> Candidate:
    target = conditional_fmax(rows)
    return min(rows, key=lambda row: (
        abs(row.fmax_mhz - target), -row.count, row.module))


def structural_section(
        arms: Mapping[str, ArmEvidence],
        designs: Mapping[str, DesignMeta]) -> dict[str, Any]:
    add_structural_features(arms)
    by_arm = {arm: candidates_by_design(arms[arm])
              for arm in STRUCTURAL_ARMS}
    common = [design for design in designs
              if all(by_arm[arm].get(design) for arm in STRUCTURAL_ARMS)]
    require(common, "no common structural support")

    per_design: dict[str, Any] = OrderedDict()
    for design in common:
        row: dict[str, Any] = {
            "family": designs[design].family,
            "regime": designs[design].regime,
            "arms": OrderedDict(),
        }
        for arm in STRUCTURAL_ARMS:
            candidates = by_arm[arm][design]
            row["arms"][arm] = {
                "n_correct_draws": sum(item.count for item in candidates),
                "n_distinct_correct": len(candidates),
                "conditional_fmax_mhz": conditional_fmax(candidates),
                "features": {
                    feature: weighted_feature(candidates, feature)
                    for feature in STRUCT_FEATURES
                },
            }
        per_design[design] = row

    aggregate: dict[str, Any] = OrderedDict()
    for feature in STRUCT_FEATURES:
        means = {
            arm: statistics.mean(
                per_design[design]["arms"][arm]["features"][feature]
                for design in common)
            for arm in STRUCTURAL_ARMS
        }
        aggregate[feature] = {
            "sft": means["sft"],
            "rf": means["rf"],
            "correctness": means["correctness"],
            "correctness_minus_sft": means["correctness"] - means["sft"],
            "rf_minus_sft": means["rf"] - means["sft"],
        }

    losses = []
    for design in common:
        sft_fmax = per_design[design]["arms"]["sft"]["conditional_fmax_mhz"]
        corr_fmax = per_design[design]["arms"]["correctness"]["conditional_fmax_mhz"]
        losses.append((corr_fmax - sft_fmax, design))
    selected_difference, selected_design = min(losses, key=lambda row: (row[0], row[1]))

    representatives: dict[str, Any] = OrderedDict()
    for arm in STRUCTURAL_ARMS:
        candidate = representative_candidate(by_arm[arm][selected_design])
        representatives[arm] = {
            "module": candidate.module,
            "multiplicity": candidate.count,
            "fmax_mhz": candidate.fmax_mhz,
            "implemented": candidate.implemented,
            "features": candidate.features,
            "rtl_source": span(candidate.rtl_path),
            "manifest_source": candidate.manifest_source,
            "ppa_source": candidate.ppa_source,
        }

    return {
        "status": "post-primary deterministic descriptive analysis",
        "conditioning": "oracle-correct endpoint RTL only",
        "canonicalizer_backend": "lexical",
        "canonicalizer_source": span(CANONICALIZER),
        "weighting": ("candidate multiplicity within design, then equal weight "
                      "over designs with correct support in SFT, RF, and correctness-only"),
        "common_support_designs": common,
        "n_common_support_designs": len(common),
        "aggregate_features": aggregate,
        "per_design": per_design,
        "selected_case": {
            "selection_rule": ("argmin over common-support designs of "
                               "correctness-only minus SFT conditional Fmax; "
                               "lexicographic design-name tie break"),
            "design": selected_design,
            "family": designs[selected_design].family,
            "regime": designs[selected_design].regime,
            "correctness_minus_sft_conditional_fmax_mhz": selected_difference,
            "sft_conditional_fmax_mhz": per_design[selected_design]["arms"]["sft"]["conditional_fmax_mhz"],
            "rf_conditional_fmax_mhz": per_design[selected_design]["arms"]["rf"]["conditional_fmax_mhz"],
            "correctness_conditional_fmax_mhz": per_design[selected_design]["arms"]["correctness"]["conditional_fmax_mhz"],
            "representative_rule": ("candidate nearest its arm's multiplicity-weighted "
                                    "conditional Fmax; then greater multiplicity; then module name"),
            "representatives": representatives,
        },
        "interpretation_boundary": (
            "These lexical structures characterize retained correct endpoint RTL. "
            "They do not include incorrect draws, prove a unique causal mechanism, "
            "or establish that every correctness-only sample is a wide combinational block."),
    }


def empirical_draw_values(arm: ArmEvidence, design: str) -> list[float]:
    values: list[float] = []
    for candidate in arm.candidates:
        if candidate.design == design:
            values.extend([candidate.fmax_mhz] * candidate.count)
    values.extend([0.0] * (arm.draws_by_design[design] - len(values)))
    require(len(values) == arm.draws_by_design[design],
            f"empirical draw accounting failed for {arm.name}/{design}")
    return values


def expected_best(values: Sequence[float], n_draws: int) -> float:
    require(values and n_draws > 0, "expected_best requires data and N>0")
    counts = Counter(float(value) for value in values)
    total = float(len(values))
    cumulative = 0
    result = 0.0
    for value, count in sorted(counts.items()):
        lo = (cumulative / total) ** n_draws
        cumulative += count
        hi = (cumulative / total) ** n_draws
        result += value * (hi - lo)
    return result


def content_probabilities(arm: ArmEvidence, design: str) -> list[float]:
    counts: dict[str, int] = defaultdict(int)
    for candidate in arm.candidates:
        if candidate.design == design:
            counts[candidate.content_key] += candidate.count
    denominator = arm.draws_by_design[design]
    return [count / denominator for count in counts.values()]


def expected_distinct_correct(probabilities: Sequence[float], n_draws: int) -> float:
    return sum(1.0 - (1.0 - probability) ** n_draws
               for probability in probabilities)


def cost_axes(
        arm: ArmEvidence, selected_designs: Sequence[str], n_draws: int,
        oracle_streams: int) -> dict[str, Any]:
    q_by_design = [arm.correct_by_design[design] /
                   arm.draws_by_design[design] for design in selected_designs]
    raw_correct_per_design = statistics.mean(n_draws * q for q in q_by_design)
    distinct_per_design = statistics.mean(
        expected_distinct_correct(content_probabilities(arm, design), n_draws)
        for design in selected_designs)
    result = {
        "llm_draws_per_design": n_draws,
        "llm_draws_total": n_draws * len(selected_designs),
        "oracle_candidate_checks_without_cache_per_design": n_draws,
        "oracle_candidate_checks_without_cache_total": n_draws * len(selected_designs),
        "oracle_simulation_streams_per_design": n_draws * oracle_streams,
        "oracle_simulation_streams_total": n_draws * oracle_streams * len(selected_designs),
        "expected_raw_correct_draws_requiring_implementation_without_cache_per_design": raw_correct_per_design,
        "expected_raw_correct_draws_requiring_implementation_without_cache_total": raw_correct_per_design * len(selected_designs),
        "expected_content_deduplicated_correct_implementations_per_design": distinct_per_design,
        "expected_content_deduplicated_correct_implementations_total": distinct_per_design * len(selected_designs),
    }
    require(distinct_per_design <= raw_correct_per_design + 1e-12,
            "deduplicated implementation count exceeds raw correct draws")
    return result


def crossing(curve: Mapping[str, float], target: float) -> dict[str, Any]:
    upper = next((n for n in BEST_OF_NS if curve[str(n)] >= target), None)
    if upper is None:
        return {
            "status": "above_observed_sft_best_of_48",
            "lower_n": 48,
            "lower_fmax_mhz": curve["48"],
            "upper_n": None,
            "upper_fmax_mhz": None,
            "log_interpolated_equivalent_n": None,
        }
    if upper == 1:
        return {
            "status": "at_or_below_sft_best_of_1",
            "lower_n": None,
            "lower_fmax_mhz": None,
            "upper_n": 1,
            "upper_fmax_mhz": curve["1"],
            "log_interpolated_equivalent_n": 1.0,
        }
    lower = upper - 1
    y0, y1 = curve[str(lower)], curve[str(upper)]
    require(y0 < target <= y1 + 1e-12 and y1 > y0,
            "invalid best-of-N crossing bracket")
    fraction = (target - y0) / (y1 - y0)
    equivalent = math.exp(math.log(lower) +
                          fraction * (math.log(upper) - math.log(lower)))
    return {
        "status": "bracketed",
        "lower_n": lower,
        "lower_fmax_mhz": y0,
        "upper_n": upper,
        "upper_fmax_mhz": y1,
        "log_interpolated_equivalent_n": equivalent,
    }


def best_of_n_section(
        arms: Mapping[str, ArmEvidence],
        designs: Mapping[str, DesignMeta]) -> dict[str, Any]:
    sft, rf = arms["sft"], arms["rf"]
    oracle_streams = {directory.oracle_streams
                      for directory in sft.directories + rf.directories}
    require(oracle_streams == {2}, "best-of-N arms use different oracle streams")
    section: dict[str, Any] = {
        "status": "post-primary empirical resampling analysis",
        "selector": ("perfect selector using true retained post-route Fmax; "
                     "an unattainable upper bound on practical reranking"),
        "sampling_model": ("with-replacement draws from each design's observed "
                           "48-draw empirical distribution; incorrect and implementation-failed draws are 0 MHz"),
        "cost_axis_boundary": ("Draw and oracle counts are exact workload units. "
                               "Raw-correct and deduplicated implementation counts are empirical expectations. "
                               "Actual generated-token and GPU-second costs are unavailable because all raw generations and timings were not retained."),
        "scopes": OrderedDict(),
    }
    for scope in ("all", "interp", "extrap"):
        selected = scope_designs(designs, scope)
        curve = OrderedDict()
        for n in BEST_OF_NS:
            curve[str(n)] = statistics.mean(
                expected_best(empirical_draw_values(sft, design), n)
                for design in selected)
        rf_one = statistics.mean(
            expected_best(empirical_draw_values(rf, design), 1)
            for design in selected)
        bracket = crossing(curve, rf_one)
        costs = OrderedDict(
            (str(n), cost_axes(sft, selected, n, 2)) for n in BEST_OF_NS)
        scope_result: dict[str, Any] = {
            "n_designs": len(selected),
            "designs": selected,
            "rf_one_draw_penalized_fmax_mhz": rf_one,
            "sft_perfect_selector_expected_fmax_mhz": curve,
            "rf_one_draw_sft_best_of_n_crossing": bracket,
            "sft_cost_axes": costs,
            "rf_one_draw_cost_axes": cost_axes(rf, selected, 1, 2),
        }
        if bracket["upper_n"] is not None:
            scope_result["cost_at_crossing_upper_n"] = costs[str(bracket["upper_n"])]
        else:
            scope_result["cost_at_crossing_upper_n"] = None
        section["scopes"][scope] = scope_result
    return section


def identity_record(path: pathlib.Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "sha256_lf": sha256_lf(path),
        "lines": line_count(path),
        "source": span(path),
    }


def input_identity(arms: Mapping[str, ArmEvidence]) -> dict[str, Any]:
    core_paths = {SEALED_SPLIT, SEALED_RESULTS, PPA_AUDIT, CANONICALIZER}
    for arm in arms.values():
        for directory in arm.directories:
            core_paths.update(path for path in directory.input_paths
                              if path.suffix != ".sv")
    core = [identity_record(path) for path in sorted(core_paths)]
    structural: dict[str, Any] = OrderedDict()
    for arm_name in STRUCTURAL_ARMS:
        paths = sorted({candidate.rtl_path for candidate in arms[arm_name].candidates})
        members = [identity_record(path) for path in paths]
        structural[arm_name] = {
            "n_files": len(members),
            "combined_sha256": combined_digest(
                (row["path"], row["sha256_lf"]) for row in members),
            "members": members,
        }
    return {"core_files": core, "structural_rtl_corpora": structural}


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def provenance_markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Artifact-only extension provenance",
        "",
        "> AUTO-GENERATED by `analyze_artifact_extension.py`. Do not hand edit.",
        "",
        "This package is a deterministic post-primary analysis of the completed",
        "sealed Study 2 artifacts. It performs no training, generation, oracle",
        "execution, Vivado run, checkpoint selection, or manuscript mutation.",
        "",
        "## Exact decomposition",
        "",
        "| Arm | Correct q | Conditional mu [MHz] | Penalized Fmax [MHz] | Residual [MHz] |",
        "|---|---:|---:|---:|---:|",
    ]
    for arm, row in payload["decomposition"]["arms"].items():
        all_row = row["all"]
        lines.append(
            f"| {arm} | {all_row['q_correct']:.6f} | "
            f"{all_row['mu_fmax_given_correct_mhz']:.6f} | "
            f"{all_row['penalized_fmax_mhz']:.6f} | "
            f"{all_row['identity_residual_mhz']:.3e} |")

    structural = payload["correctness_structure"]
    lines.extend([
        "",
        "## Correctness-only structural characterization",
        "",
        f"Common support: {structural['n_common_support_designs']} designs.",
        "Candidate multiplicity is preserved within design; designs are then equally weighted.",
        "All features use the frozen lexical canonicalizer.",
        "",
        "| Feature | SFT | RF | Correctness | Correctness - SFT |",
        "|---|---:|---:|---:|---:|",
    ])
    for feature, row in structural["aggregate_features"].items():
        lines.append(
            f"| `{feature}` | {fmt(row['sft'])} | {fmt(row['rf'])} | "
            f"{fmt(row['correctness'])} | {fmt(row['correctness_minus_sft'])} |")
    case = structural["selected_case"]
    lines.extend([
        "",
        "### Deterministically selected case",
        "",
        f"Selection rule: {case['selection_rule']}.",
        f"Selected design: `{case['design']}` ({case['family']}, {case['regime']}).",
        f"Correctness-only minus SFT conditional Fmax: "
        f"{case['correctness_minus_sft_conditional_fmax_mhz']:.6f} MHz.",
        "",
        "| Arm | Representative module | Multiplicity | Fmax [MHz] | RTL source | PPA source |",
        "|---|---|---:|---:|---|---|",
    ])
    for arm, row in case["representatives"].items():
        lines.append(
            f"| {arm} | `{row['module']}` | {row['multiplicity']} | "
            f"{row['fmax_mhz']:.6f} | `{row['rtl_source']}` | `{row['ppa_source']}` |")

    lines.extend([
        "",
        "## Sealed best-of-N and cost axes",
        "",
        "| Scope | RF one draw [MHz] | SFT crossing | SFT upper [MHz] | Raw correct impl./design | Deduplicated impl./design |",
        "|---|---:|---|---:|---:|---:|",
    ])
    for scope, row in payload["best_of_n"]["scopes"].items():
        cross = row["rf_one_draw_sft_best_of_n_crossing"]
        if cross["upper_n"] is None:
            label = ">48"
            upper_fmax = row["sft_perfect_selector_expected_fmax_mhz"]["48"]
            cost = row["sft_cost_axes"]["48"]
        else:
            label = (str(cross["upper_n"]) if cross["lower_n"] is None else
                     f"{cross['lower_n']}-{cross['upper_n']}")
            upper_fmax = cross["upper_fmax_mhz"]
            cost = row["cost_at_crossing_upper_n"]
        lines.append(
            f"| {scope} | {row['rf_one_draw_penalized_fmax_mhz']:.6f} | "
            f"{label} | {upper_fmax:.6f} | "
            f"{cost['expected_raw_correct_draws_requiring_implementation_without_cache_per_design']:.6f} | "
            f"{cost['expected_content_deduplicated_correct_implementations_per_design']:.6f} |")

    lines.extend([
        "",
        "## Input identities",
        "",
        "Every core input and every RTL file used by the structural aggregate is",
        "hashed in `artifact_extension_results.json`. The compact core ledger is:",
        "",
        "| Path | SHA-256 (LF-normalized) | Source |",
        "|---|---|---|",
    ])
    for row in payload["input_identity"]["core_files"]:
        lines.append(f"| `{row['path']}` | `{row['sha256_lf']}` | `{row['source']}` |")
    lines.extend(["", "Structural RTL corpus identities:", ""])
    for arm, row in payload["input_identity"]["structural_rtl_corpora"].items():
        lines.append(
            f"- {arm}: {row['n_files']} files, combined SHA-256 "
            f"`{row['combined_sha256']}`; every member path/hash/span is enumerated "
            "in the JSON result.")

    lines.extend([
        "",
        "## Interpretation limits",
        "",
        "- The analysis is post-primary and cannot alter the frozen Study 2 outcome.",
        "- Structural results condition on oracle-correct retained RTL; incorrect raw generations were not retained.",
        "- The best-of-N curve resamples the observed empirical distribution and uses a perfect real-Fmax selector.",
        "- Content deduplication assumes candidates with the same recorded source SHA-256 require one implementation.",
        "- Actual token counts and GPU seconds cannot be reconstructed from the retained sealed artifacts.",
        "- Fmax remains the original 5 ns WNS-derived value, not an independently validated clock-closure boundary.",
        "",
    ])
    return "\n".join(lines)


def build_package() -> tuple[dict[str, Any], str]:
    designs = load_split()
    arms = combine_arms(designs)
    validate_against_sealed_results(arms, designs)
    decomposition = decomposition_section(arms, designs)
    correctness_structure = structural_section(arms, designs)
    best_of_n = best_of_n_section(arms, designs)
    payload: dict[str, Any] = OrderedDict([
        ("schema", "artifact_extension_results/1"),
        ("status", "post-primary deterministic artifact-only analysis"),
        ("immutability", {
            "new_training": False,
            "new_generation": False,
            "new_oracle_execution": False,
            "new_vivado_execution": False,
            "checkpoint_or_sample_selection": False,
            "changes_sealed_study2_outcome": False,
            "original_outcome": read_json(SEALED_RESULTS)["outcome"],
        }),
        ("decomposition", decomposition),
        ("correctness_structure", correctness_structure),
        ("best_of_n", best_of_n),
        ("input_identity", input_identity(arms)),
        ("generator", {
            "path": rel(pathlib.Path(__file__)),
            "sha256_lf": sha256_lf(pathlib.Path(__file__)),
        }),
    ])
    return payload, provenance_markdown(payload)


def rendered_outputs() -> dict[pathlib.Path, str]:
    payload, provenance = build_package()
    result_text = json.dumps(payload, indent=2, sort_keys=False,
                             ensure_ascii=True) + "\n"
    return {RESULT_PATH: result_text, PROVENANCE_PATH: provenance}


def check_outputs(outputs: Mapping[pathlib.Path, str]) -> None:
    failures = []
    for path, expected in outputs.items():
        if not path.exists():
            failures.append(f"missing {rel(path)}")
            continue
        actual = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if actual != expected:
            failures.append(f"stale {rel(path)}")
    if failures:
        raise ArtifactExtensionError("; ".join(failures))


def write_outputs(outputs: Mapping[pathlib.Path, str]) -> None:
    for path, content in outputs.items():
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8", newline="\n")
        os.replace(temporary, path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail unless committed outputs exactly match regeneration")
    args = parser.parse_args(argv)
    try:
        outputs = rendered_outputs()
        if args.check:
            check_outputs(outputs)
            print("artifact extension: PASS (inputs valid; outputs current)")
        else:
            write_outputs(outputs)
            payload = json.loads(outputs[RESULT_PATH])
            all_decomp = payload["decomposition"]["arms"]
            crossing_all = payload["best_of_n"]["scopes"]["all"][
                "rf_one_draw_sft_best_of_n_crossing"]
            print(f"wrote {rel(RESULT_PATH)} and {rel(PROVENANCE_PATH)}")
            print("decomposition:")
            for arm, row in all_decomp.items():
                value = row["all"]
                print(f"  {arm:11s} q={value['q_correct']:.6f} "
                      f"mu={value['mu_fmax_given_correct_mhz']:.6f} "
                      f"F={value['penalized_fmax_mhz']:.6f}")
            print("sealed all-design RF-one-draw crossing: "
                  f"SFT best-of-{crossing_all['lower_n']} to "
                  f"best-of-{crossing_all['upper_n']}")
    except ArtifactExtensionError as exc:
        print(f"artifact extension: FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
