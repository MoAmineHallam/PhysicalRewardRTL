#!/usr/bin/env python3
"""Fail-closed analysis for preregistration revision 3.

This file corrects implementation defects in the frozen revision-2 script
without replacing it.  It must be hashed, tested, and recorded as a
pre-outcome amendment before any sealed result is opened.

Input contract
--------------
Each evaluation directory contains ``fmax_manifest.json`` and ``ppa.jsonl``.
The manifest contains one row per distinct oracle-correct candidate, with its
sample multiplicity in ``count`` and the total generations for that design in
``n`` (``n_samples`` is accepted for compatibility).  A
``holdout_summary.json`` may establish ``n`` for a design with zero correct
candidates.  For the SFT and rf_struct directories, every correct-candidate
row must also contain ``reward`` (or ``predicted_reward``), the rf_struct
prediction in MHz.  Incorrect/extraction-failed samples have reward zero.

The primary rf_struct endpoint has two 24-sample directories, one per training
seed.  The optional update-138 evaluation likewise has two 8-sample
directories.  Missing designs, missing seeds, inconsistent sample counts,
mixed policies, duplicate modules, and malformed PPA records are fatal; no
design or seed is silently dropped.

The rf_struct training group logs and the pre-open canonicalisation/trace
contract are required.  Reward resolution, policy-update completion, and the
validity gate are derived from those artifacts rather than entered by hand.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np


HERE = os.path.dirname(os.path.abspath(__file__))
N_BOOT = 100_000
CI = 0.95
BOOT_SEED = 20260813
ENDPOINT_SAMPLES = 24
SFT_SAMPLES = 48
MID_SAMPLES = 8
EXPECTED_RF_SEEDS = 2
TARGET_UPDATES = 276
GROUP_SIZE = 8
RETENTION_THRESHOLD = 0.50
MATERIAL_MHZ = 5.0
MATERIAL_FRAC = 0.02


class AnalysisInputError(ValueError):
    """An input violates the frozen evaluation contract."""


def _sha256_text_file(path: str) -> str:
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        raise AnalysisInputError(f"cannot hash {path}: {exc}") from exc
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


def _sha256_raw_file(path: str) -> str:
    try:
        with open(path, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError as exc:
        raise AnalysisInputError(f"cannot hash {path}: {exc}") from exc


def _read_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        raise AnalysisInputError(f"cannot read valid JSON {path}: {exc}") from exc


def _finite_number(value: Any, what: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise AnalysisInputError(f"{what} is not numeric: {value!r}") from exc
    if not math.isfinite(out):
        raise AnalysisInputError(f"{what} is not finite: {value!r}")
    return out


def _positive_int(value: Any, what: str) -> int:
    if isinstance(value, bool):
        raise AnalysisInputError(f"{what} is not a positive integer: {value!r}")
    try:
        out = int(value)
    except (TypeError, ValueError) as exc:
        raise AnalysisInputError(
            f"{what} is not a positive integer: {value!r}") from exc
    if out <= 0 or float(value) != out:
        raise AnalysisInputError(f"{what} is not a positive integer: {value!r}")
    return out


def material_change(a: float, b: float) -> bool:
    """The already-declared max(5 MHz, 2%) materiality rule."""
    return abs(a - b) > max(MATERIAL_MHZ,
                            MATERIAL_FRAC * max(abs(a), abs(b)))


def load_sealed(path: str) -> Tuple[dict, List[str], Dict[str, Tuple[str, str]]]:
    sealed = _read_json(path)
    rows = sealed.get("designs") if isinstance(sealed, dict) else None
    if not isinstance(rows, list) or not rows:
        raise AnalysisInputError("sealed split has no designs list")
    expected_n = int(sealed.get("n_designs", len(rows)))
    if len(rows) != expected_n:
        raise AnalysisInputError(
            f"sealed split says {expected_n} designs but contains {len(rows)}")
    designs: List[str] = []
    meta: Dict[str, Tuple[str, str]] = {}
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise AnalysisInputError(f"sealed design row {i} is not an object")
        design = row.get("design")
        family = row.get("family")
        regime = row.get("regime")
        if not all(isinstance(x, str) and x for x in (design, family, regime)):
            raise AnalysisInputError(f"sealed design row {i} lacks metadata")
        if regime not in ("interp", "extrap"):
            raise AnalysisInputError(f"unknown regime for {design}: {regime}")
        if design in meta:
            raise AnalysisInputError(f"duplicate sealed design: {design}")
        designs.append(design)
        meta[design] = (family, regime)
    return sealed, designs, meta


def _manifest_items(manifest: Any, path: str) -> List[Tuple[str, dict]]:
    if isinstance(manifest, dict):
        items = list(manifest.items())
    elif isinstance(manifest, list):
        items = []
        for i, row in enumerate(manifest):
            if not isinstance(row, dict) or not isinstance(row.get("module"), str):
                raise AnalysisInputError(f"invalid manifest row {i} in {path}")
            items.append((row["module"], row))
    else:
        raise AnalysisInputError(f"manifest {path} is neither object nor list")
    seen = set()
    for module, row in items:
        if not isinstance(module, str) or not module or not isinstance(row, dict):
            raise AnalysisInputError(f"invalid module row in {path}: {module!r}")
        if module in seen:
            raise AnalysisInputError(f"duplicate manifest module {module} in {path}")
        seen.add(module)
    return items


def validate_generation_config(directory: str, *, policy: str,
                               training_seed: int, generation_seed: int,
                               n: int, score_rf: bool, checkpoint: str) -> dict:
    path = os.path.join(directory, "generation_config.json")
    config = _read_json(path)
    expected = {
        "schema": "sealed_evaluation/1", "policy": policy,
        "training_seed": training_seed, "generation_seed": generation_seed,
        "n_per_design": n, "temperature": 1.0, "gen_batch": 4,
        "oracle_seeds": [1, 2], "oracle_n": 1024,
        "score_rf": score_rf,
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise AnalysisInputError(
                f"{path} {key}: expected {value!r}, got {config.get(key)!r}")
    actual_adapter = os.path.normpath(config.get("adapter", "")).replace("\\", "/")
    expected_adapter = os.path.normpath(checkpoint).replace("\\", "/")
    if not actual_adapter.endswith(expected_adapter):
        raise AnalysisInputError(
            f"{path} adapter is not the declared {checkpoint} checkpoint")
    sealed_path = config.get("sealed_split")
    if not isinstance(sealed_path, str) or not os.path.isfile(sealed_path):
        # Linux absolute paths are not meaningful after artifacts move to the
        # laptop, so fall back to the canonical local split and verify its hash.
        sealed_path = os.path.join(HERE, "sealed_split.json")
    if config.get("sealed_split_sha256") != _sha256_text_file(sealed_path):
        raise AnalysisInputError(f"{path} sealed-split hash mismatch")
    if config.get("eval_script_sha256") != _sha256_text_file(
            os.path.join(HERE, "eval_sealed.py")):
        raise AnalysisInputError(f"{path} evaluator hash mismatch")
    if score_rf and config.get("rf_artifact_sha256") != _sha256_raw_file(
            os.path.join(HERE, "rf_struct.joblib")):
        raise AnalysisInputError(f"{path} RF artifact hash mismatch")
    return config


def _summary_counts(directory: str, designs: Sequence[str]) -> Dict[str, int]:
    """Read generation counts, including designs with zero correct outputs.

    Existing evaluators write ``holdout_summary.json`` as policy -> design ->
    metrics.  A direct design -> metrics mapping is also accepted.  Ambiguous
    duplicate entries are rejected.
    """
    path = os.path.join(directory, "holdout_summary.json")
    if not os.path.exists(path):
        return {}
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise AnalysisInputError(f"{path} is not an object")
    wanted = set(designs)
    candidates: List[Mapping[str, Any]] = []
    if wanted.intersection(raw):
        candidates.append(raw)
    for value in raw.values():
        if isinstance(value, dict) and wanted.intersection(value):
            candidates.append(value)
    out: Dict[str, int] = {}
    for mapping in candidates:
        for design in wanted.intersection(mapping):
            row = mapping[design]
            if not isinstance(row, dict):
                raise AnalysisInputError(f"summary row for {design} is not an object")
            n_value = row.get("n_samples", row.get("n"))
            if n_value is None:
                continue
            n = _positive_int(n_value, f"summary n for {design}")
            if design in out and out[design] != n:
                raise AnalysisInputError(
                    f"ambiguous summary sample counts for {design}: "
                    f"{out[design]} vs {n}")
            out[design] = n
    return out


def _row_total_samples(row: Mapping[str, Any], module: str) -> Optional[int]:
    values = []
    for key in ("n", "n_samples"):
        if row.get(key) is not None:
            values.append(_positive_int(row[key], f"{key} for {module}"))
    if len(set(values)) > 1:
        raise AnalysisInputError(f"n and n_samples disagree for {module}")
    return values[0] if values else None


def _load_ppa(path: str, manifest_modules: set) -> Dict[str, Optional[float]]:
    if not os.path.exists(path):
        raise AnalysisInputError(f"missing required synthesis results: {path}")
    out: Dict[str, Optional[float]] = {}
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError as exc:
                raise AnalysisInputError(f"malformed JSON at {path}:{lineno}") from exc
            module = row.get("module") if isinstance(row, dict) else None
            if not isinstance(module, str) or not module:
                raise AnalysisInputError(f"missing module at {path}:{lineno}")
            if module not in manifest_modules:
                raise AnalysisInputError(
                    f"PPA module {module} is absent from {path}'s manifest")
            if module in out:
                raise AnalysisInputError(f"duplicate PPA result for {module}")
            if row.get("compiled"):
                if row.get("fmax_mhz") is None:
                    raise AnalysisInputError(f"compiled PPA row lacks Fmax: {module}")
                fmax = _finite_number(row["fmax_mhz"], f"Fmax for {module}")
                if fmax < 0:
                    raise AnalysisInputError(f"negative Fmax for {module}: {fmax}")
                out[module] = fmax
            else:
                out[module] = None
    missing = manifest_modules - set(out)
    if missing:
        raise AnalysisInputError(
            f"missing explicit PPA rows for {len(missing)} manifest modules: "
            f"{sorted(missing)[:5]}")
    return out


def load_eval_dir(directory: str, designs: Sequence[str],
                  meta: Mapping[str, Tuple[str, str]], expected_n: int,
                  require_reward: bool = False) -> Dict[str, dict]:
    """Load one complete evaluation replicate; never drop a design."""
    manifest_path = os.path.join(directory, "fmax_manifest.json")
    if not os.path.exists(manifest_path):
        raise AnalysisInputError(f"missing manifest: {manifest_path}")
    items = _manifest_items(_read_json(manifest_path), manifest_path)
    wanted = set(designs)
    summary_n = _summary_counts(directory, designs)
    policies = {row.get("policy") for _, row in items if row.get("policy")}
    if len(policies) > 1:
        raise AnalysisInputError(
            f"evaluation directory mixes policies {sorted(policies)}: {directory}")

    agg = {design: {"sum_fmax": 0.0, "correct": 0, "compiled": 0,
                    "n_values": set(), "sum_reward": 0.0,
                    "reward_rows": 0, "modules": 0}
           for design in designs}
    manifest_modules = set()
    row_by_module: Dict[str, dict] = {}
    for module, row in items:
        design = row.get("design")
        if design not in wanted:
            raise AnalysisInputError(
                f"manifest contains non-sealed design {design!r}: {module}")
        family, regime = meta[design]
        if row.get("family") is not None and row["family"] != family:
            raise AnalysisInputError(f"family mismatch for {module}")
        if row.get("regime") is not None and row["regime"] != regime:
            raise AnalysisInputError(f"regime mismatch for {module}")
        count = _positive_int(row.get("count", 1), f"count for {module}")
        n = _row_total_samples(row, module)
        if n is not None:
            agg[design]["n_values"].add(n)
        reward_keys = [key for key in ("reward", "predicted_reward")
                       if row.get(key) is not None]
        if len(reward_keys) == 2:
            a = _finite_number(row["reward"], f"reward for {module}")
            b = _finite_number(row["predicted_reward"],
                               f"predicted_reward for {module}")
            if not math.isclose(a, b, rel_tol=0.0, abs_tol=1e-9):
                raise AnalysisInputError(f"reward aliases disagree for {module}")
        reward = None
        if reward_keys:
            reward = _finite_number(row[reward_keys[0]], f"reward for {module}")
            if reward < 0:
                raise AnalysisInputError(f"negative reward for {module}: {reward}")
            agg[design]["sum_reward"] += count * reward
            agg[design]["reward_rows"] += 1
        elif require_reward:
            raise AnalysisInputError(f"rf_struct reward missing for {module}")
        agg[design]["correct"] += count
        agg[design]["modules"] += 1
        manifest_modules.add(module)
        row_by_module[module] = {"design": design, "count": count,
                                 "reward": reward}

    ppa = _load_ppa(os.path.join(directory, "ppa.jsonl"), manifest_modules)
    for module, row in row_by_module.items():
        fmax = ppa.get(module)
        if fmax is not None:
            a = agg[row["design"]]
            a["sum_fmax"] += row["count"] * fmax
            a["compiled"] += row["count"]

    out: Dict[str, dict] = {}
    for design in designs:
        a = agg[design]
        if design in summary_n:
            a["n_values"].add(summary_n[design])
        if len(a["n_values"]) != 1:
            reason = "missing" if not a["n_values"] else "inconsistent"
            raise AnalysisInputError(
                f"{reason} total sample count for {design} in {directory}; "
                "zero-correct designs require holdout_summary.json")
        n = next(iter(a["n_values"]))
        if n != expected_n:
            raise AnalysisInputError(
                f"{design} has n={n} in {directory}; expected {expected_n}")
        if a["correct"] > n:
            raise AnalysisInputError(
                f"correct multiplicity {a['correct']} exceeds n={n} for {design}")
        if a["compiled"] > a["correct"]:
            raise AnalysisInputError(f"compiled multiplicity exceeds correct: {design}")
        # If a design has no correct candidates its rf_struct reward is exactly
        # zero, so no candidate row is needed to establish reward availability.
        reward_available = require_reward or (
            a["modules"] > 0 and a["reward_rows"] == a["modules"])
        out[design] = {
            "equal": a["sum_fmax"] / n,
            "cond_correct": (a["sum_fmax"] / a["correct"]
                             if a["correct"] else 0.0),
            "cond_compiled": (a["sum_fmax"] / a["compiled"]
                              if a["compiled"] else 0.0),
            "correct_rate": a["correct"] / n,
            "synth_rate": a["compiled"] / n,
            "n_correct": a["correct"],
            "n_compiled": a["compiled"],
            "n_distinct_correct": a["modules"],
            "n_samples": n,
            "reward_equal": (a["sum_reward"] / n
                             if reward_available else None),
        }
    return out


@dataclass
class ArmData:
    combined: Dict[str, dict]
    seeds: List[Dict[str, dict]]
    directories: List[str]


def load_arm(directories: Sequence[str], designs: Sequence[str],
             meta: Mapping[str, Tuple[str, str]], expected_n: int,
             expected_replicates: Optional[Iterable[int]] = None,
             require_reward: bool = False) -> ArmData:
    dirs = [os.path.abspath(d) for d in directories]
    if not dirs or len(set(dirs)) != len(dirs):
        raise AnalysisInputError("arm directories are empty or duplicated")
    if expected_replicates is not None and len(dirs) not in set(expected_replicates):
        allowed = sorted(set(expected_replicates))
        raise AnalysisInputError(
            f"arm has {len(dirs)} replicate(s); expected one of {allowed}")
    seeds = [load_eval_dir(d, designs, meta, expected_n, require_reward)
             for d in dirs]
    combined: Dict[str, dict] = {}
    metrics = ("equal", "cond_correct", "cond_compiled", "correct_rate",
               "synth_rate", "reward_equal")
    for design in designs:
        row = {"n_seeds": len(seeds)}
        for metric in metrics:
            values = [seed[design][metric] for seed in seeds]
            row[metric] = (None if any(v is None for v in values)
                           else float(np.mean(values)))
        combined[design] = row
    return ArmData(combined=combined, seeds=seeds, directories=dirs)


@dataclass
class BootstrapPlan:
    designs: List[str]
    picks: np.ndarray
    digest: str


def make_bootstrap_plans(designs: Sequence[str],
                         meta: Mapping[str, Tuple[str, str]],
                         n_boot: int = N_BOOT,
                         seed: int = BOOT_SEED) -> Dict[str, BootstrapPlan]:
    """Generate one immutable resample plan reused by every arm."""
    rng = np.random.default_rng(seed)
    plans: Dict[str, BootstrapPlan] = {}
    for scope in ("interp", "extrap", "all"):
        scoped = [d for d in designs if scope == "all" or meta[d][1] == scope]
        positions = collections.defaultdict(list)
        for pos, design in enumerate(scoped):
            positions[meta[design]].append(pos)
        chunks = []
        for stratum in sorted(positions):
            group = np.asarray(positions[stratum], dtype=np.int16)
            draw = rng.integers(0, len(group), size=(n_boot, len(group)))
            chunks.append(group[draw])
        picks = np.concatenate(chunks, axis=1) if chunks else np.empty(
            (n_boot, 0), dtype=np.int16)
        digest = hashlib.sha256(picks.tobytes()).hexdigest()
        plans[scope] = BootstrapPlan(scoped, picks, digest)
    return plans


def bootstrap_ci(diff_by_design: Mapping[str, float], plan: BootstrapPlan,
                 ci: float = CI) -> Tuple[float, float, float]:
    values = np.asarray([diff_by_design[d] for d in plan.designs], dtype=float)
    if not len(values):
        raise AnalysisInputError("bootstrap scope has no designs")
    stats = values[plan.picks].mean(axis=1)
    alpha = (1.0 - ci) / 2.0
    return (float(values.mean()), float(np.quantile(stats, alpha)),
            float(np.quantile(stats, 1.0 - alpha)))


def _scope_designs(designs: Sequence[str], meta: Mapping[str, Tuple[str, str]],
                   scope: str) -> List[str]:
    return [d for d in designs if scope == "all" or meta[d][1] == scope]


def report_arm(arm: ArmData, sft: ArmData, designs: Sequence[str],
               meta: Mapping[str, Tuple[str, str]],
               plans: Mapping[str, BootstrapPlan]) -> dict:
    report: Dict[str, Any] = {"combined": {}, "per_seed": []}
    for scope in ("interp", "extrap", "all"):
        ds = _scope_designs(designs, meta, scope)
        diffs = {d: arm.combined[d]["equal"] - sft.combined[d]["equal"]
                 for d in ds}
        mean, lo, hi = bootstrap_ci(diffs, plans[scope])
        arm_equal = float(np.mean([arm.combined[d]["equal"] for d in ds]))
        sft_equal = float(np.mean([sft.combined[d]["equal"] for d in ds]))
        report["combined"][scope] = {
            "n_designs": len(ds), "mean_diff": mean,
            "ci_lo": lo, "ci_hi": hi,
            "ci_excludes_zero": bool(lo > 0 or hi < 0),
            "arm_equal": arm_equal, "sft_equal": sft_equal,
            "material_change": material_change(arm_equal, sft_equal),
            "arm_correct": float(np.mean(
                [arm.combined[d]["correct_rate"] for d in ds])),
            "sft_correct": float(np.mean(
                [sft.combined[d]["correct_rate"] for d in ds])),
            "arm_synth_rate": float(np.mean(
                [arm.combined[d]["synth_rate"] for d in ds])),
            "sft_synth_rate": float(np.mean(
                [sft.combined[d]["synth_rate"] for d in ds])),
            "bootstrap_plan_sha256": plans[scope].digest,
        }
    for seed_data in arm.seeds:
        seed_report = {}
        for scope in ("interp", "extrap", "all"):
            ds = _scope_designs(designs, meta, scope)
            seed_report[scope] = float(np.mean([
                seed_data[d]["equal"] - sft.combined[d]["equal"] for d in ds]))
        report["per_seed"].append(seed_report)
    return report


def load_group_logs(paths: Sequence[str]) -> dict:
    """Derive Check B and update completion from both rf_struct group logs."""
    if len(paths) != EXPECTED_RF_SEEDS or len(set(map(os.path.abspath, paths))) != len(paths):
        raise AnalysisInputError("exactly two distinct rf_struct group logs are required")
    eligible = resolved = attempted = flat = 0
    distinct_rtl = set()
    seed_summaries = []
    gates = collections.Counter()
    for path in paths:
        groups: Dict[int, list] = collections.defaultdict(list)
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except ValueError as exc:
                    raise AnalysisInputError(f"malformed JSON at {path}:{lineno}") from exc
                if not isinstance(row, dict) or row.get("group_index") is None:
                    raise AnalysisInputError(f"bad group row at {path}:{lineno}")
                gi = _positive_int(row["group_index"],
                                   f"group_index at {path}:{lineno}")
                groups[gi].append(row)
                gates[str(row.get("gate"))] += 1
                if isinstance(row.get("rtl"), str) and row["rtl"]:
                    distinct_rtl.add(row["rtl"].replace("\r\n", "\n"))
        if not groups:
            raise AnalysisInputError(f"empty rf_struct group log: {path}")
        update_ids = set()
        for gi in sorted(groups):
            rows = groups[gi]
            if len(rows) != GROUP_SIZE:
                raise AnalysisInputError(
                    f"group {gi} in {path} has {len(rows)} rows; expected {GROUP_SIZE}")
            attempted += 1
            designs = {row.get("design") for row in rows}
            flat_values = {bool(row.get("flat")) for row in rows}
            updates = {row.get("update") for row in rows}
            if len(designs) != 1 or len(flat_values) != 1 or len(updates) != 1:
                raise AnalysisInputError(f"inconsistent rows within group {gi} in {path}")
            is_flat = flat_values.pop()
            update = updates.pop()
            if is_flat:
                flat += 1
                if update is not None:
                    raise AnalysisInputError(f"flat group {gi} has an update index")
            else:
                if update is None:
                    raise AnalysisInputError(f"non-flat group {gi} lacks update index")
                update_ids.add(_positive_int(update, f"update in group {gi}"))
            correct = [row for row in rows if row.get("correct") is True
                       and isinstance(row.get("struct_features"), dict)]
            vectors = {json.dumps(row["struct_features"], sort_keys=True,
                                  separators=(",", ":")) for row in correct}
            if len(vectors) >= 2:
                eligible += 1
                rewards = [_finite_number(row.get("reward"),
                                          f"reward in group {gi}")
                           for row in correct]
                if max(rewards) - min(rewards) > MATERIAL_MHZ:
                    resolved += 1
        if update_ids != set(range(1, TARGET_UPDATES + 1)):
            missing = sorted(set(range(1, TARGET_UPDATES + 1)) - update_ids)
            extra = sorted(update_ids - set(range(1, TARGET_UPDATES + 1)))
            raise AnalysisInputError(
                f"{path} does not contain exactly updates 1..{TARGET_UPDATES}; "
                f"missing={missing[:5]} extra={extra[:5]}")
        seed_summaries.append({"path": os.path.abspath(path),
                               "attempted_groups": len(groups),
                               "updates": len(update_ids)})
    fraction = resolved / eligible if eligible else 0.0
    return {
        "eligible_groups": eligible, "resolved_groups": resolved,
        "resolved_fraction": fraction, "attempted_groups": attempted,
        "flat_groups": flat, "gate_counts": dict(sorted(gates.items())),
        "distinct_rtl_candidates": len(distinct_rtl),
        "seed_summaries": seed_summaries,
    }


def load_mutation_contract(path: str, expected_candidates: int) -> dict:
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise AnalysisInputError("mutation contract is not an object")
    n = int(raw.get("n", -1))
    passed = int(raw.get("passed", -1))
    rejected = int(raw.get("rejected", -1))
    collisions = int(raw.get("collisions", -1))
    failures = raw.get("failures")
    per_file = raw.get("per_file")
    reasons = []
    if n != expected_candidates:
        reasons.append(f"audited {n} candidates; group logs contain {expected_candidates}")
    if n <= 0:
        reasons.append("no candidates audited")
    if passed != n:
        reasons.append(f"only {passed}/{n} candidates passed")
    if rejected != 0:
        reasons.append(f"{rejected} candidates rejected")
    if collisions != 0:
        reasons.append(f"{collisions} cross-design canonical collisions")
    if not isinstance(failures, dict) or any(int(v) for v in failures.values()):
        reasons.append(f"contract failures present: {failures!r}")
    if not isinstance(per_file, list) or len(per_file) != n:
        reasons.append("per-file contract evidence is missing or incomplete")
    else:
        for row in per_file:
            if (not isinstance(row, dict) or row.get("ok") is not True
                    or row.get("rejected") is True
                    or row.get("trace_equal") is not True):
                reasons.append("not every candidate passed compilation and trace equality")
                break
    return {"ok": not reasons, "reasons": reasons, "path": os.path.abspath(path),
            "n": n, "passed": passed, "rejected": rejected,
            "collisions": collisions, "failures": failures}


def reward_change(arm: ArmData, baseline: ArmData, designs: Sequence[str],
                  meta: Mapping[str, Tuple[str, str]]) -> Dict[str, dict]:
    out = {}
    for scope in ("interp", "extrap", "all"):
        ds = _scope_designs(designs, meta, scope)
        before_values = [baseline.combined[d]["reward_equal"] for d in ds]
        after_values = [arm.combined[d]["reward_equal"] for d in ds]
        if any(v is None for v in before_values + after_values):
            raise AnalysisInputError(f"rf_struct reward missing in {scope} evaluation")
        before = float(np.mean(before_values))
        after = float(np.mean(after_values))
        out[scope] = {"before": before, "after": after,
                      "difference": after - before,
                      "material": material_change(after, before),
                      "increased": after > before}
    return out


def late_divergence(mid: Optional[ArmData], end: ArmData,
                    designs: Sequence[str], meta: Mapping[str, Tuple[str, str]]) -> dict:
    if mid is None:
        return {"measured": False, "any": False, "by_regime": {}}
    by_regime = {}
    any_divergence = False
    for scope in ("interp", "extrap"):
        ds = _scope_designs(designs, meta, scope)
        mid_r = float(np.mean([mid.combined[d]["reward_equal"] for d in ds]))
        end_r = float(np.mean([end.combined[d]["reward_equal"] for d in ds]))
        mid_f = float(np.mean([mid.combined[d]["equal"] for d in ds]))
        end_f = float(np.mean([end.combined[d]["equal"] for d in ds]))
        divergent = (end_r > mid_r and material_change(end_r, mid_r)
                     and end_f < mid_f and material_change(end_f, mid_f))
        any_divergence |= divergent
        by_regime[scope] = {
            "mid_reward": mid_r, "end_reward": end_r,
            "mid_equal_fmax": mid_f, "end_equal_fmax": end_f,
            "divergent": bool(divergent),
        }
    return {"measured": True, "any": bool(any_divergence),
            "by_regime": by_regime}


def _seed_effects(report: Mapping[str, Any], regime: str) -> List[float]:
    return [float(seed[regime]) for seed in report["per_seed"]]


def classify(rf_report: Mapping[str, Any], gate: Mapping[str, Any],
             group_stats: Mapping[str, Any], reward_delta: Mapping[str, Any],
             late: Mapping[str, Any]) -> Tuple[str, str]:
    """Exhaustive revision-3 operationalisation of the frozen eight labels."""
    if not gate.get("ok"):
        return "invalid_repair", "; ".join(gate.get("reasons", []))
    resolved = float(group_stats["resolved_fraction"])
    if resolved < 0.20:
        return ("reward_resolution_failure",
                f"{100.0 * resolved:.1f}% of eligible groups resolved (<20%)")

    # Sign disagreement is checked within each regime, as the full-success rule
    # itself is regime-specific.  A zero and a nonzero effect are not opposite
    # signs; two strictly opposite effects are.
    for regime in ("interp", "extrap"):
        signs = _seed_effects(rf_report, regime)
        if len(signs) >= 2 and signs[0] * signs[1] < 0:
            return ("seed_unstable",
                    f"training-seed effect signs disagree in {regime}: {signs}")

    if late.get("any"):
        return "reward_misalignment", "material late reward-reality divergence"

    combined = rf_report["combined"]
    stable = {}
    directional = {}
    for regime in ("interp", "extrap"):
        seeds = _seed_effects(rf_report, regime)
        both_seed_positive = len(seeds) >= 2 and all(x > 0 for x in seeds)
        stable[regime] = both_seed_positive and combined[regime]["ci_lo"] > 0
        directional[regime] = (both_seed_positive
                               and combined[regime]["ci_lo"] <= 0
                               <= combined[regime]["ci_hi"])
    if all(stable.values()):
        return ("full_two_regime_repair",
                "both seeds improve in both regimes and both combined CIs exclude zero")
    if sum(stable.values()) == 1:
        good = next(regime for regime, value in stable.items() if value)
        return "regime_limited", f"stable improvement in {good} only"
    if any(directional.values()):
        scopes = [regime for regime, value in directional.items() if value]
        return ("directional_but_imprecise",
                f"both seeds improve but the combined CI includes zero in {scopes}")

    # Without a midpoint, the preregistration permits only the weaker endpoint
    # reward-reality statement.  A material reward increase paired with a
    # non-positive real-Fmax point effect is classified as misalignment.
    mismatched = []
    for regime in ("interp", "extrap"):
        rd = reward_delta[regime]
        if rd["material"] and rd["increased"] \
                and combined[regime]["mean_diff"] <= 0:
            mismatched.append(regime)
    if mismatched:
        return ("reward_misalignment",
                f"reward rose materially but real Fmax did not improve in {mismatched}")

    negligible = all(not combined[regime]["material_change"]
                     for regime in ("interp", "extrap"))
    if negligible:
        return ("stable_null",
                "valid and resolved, with no material real-Fmax change in either regime")
    return ("reward_misalignment",
            "policy updated and the remaining material real-Fmax effect was not a stable improvement")


def _parse_named_dirs(spec: str) -> Tuple[str, List[str]]:
    name, sep, raw = spec.partition("=")
    dirs = [d for d in raw.split(",") if d]
    if not sep or not name or not dirs:
        raise AnalysisInputError(f"expected name=dir[,dir2], got {spec!r}")
    return name, dirs


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sealed", default=os.path.join(HERE, "sealed_split.json"))
    ap.add_argument("--sft", required=True,
                    help="48-sample SFT evaluation directory")
    ap.add_argument("--arm", action="append", required=True,
                    help="name=seed1_dir[,seed2_dir]")
    ap.add_argument("--primary", default="rf")
    ap.add_argument("--mid", default="",
                    help="rf=update138_seed1_dir,update138_seed2_dir")
    ap.add_argument("--rf-group-log", action="append", required=True,
                    help="repeat exactly twice, once per rf_struct training seed")
    ap.add_argument("--mutation-contract", required=True,
                    help="canonicalize.py --check-traces JSON over every distinct "
                         "rf_struct training candidate")
    ap.add_argument("--out", default=os.path.join(HERE, "sealed_results_v3.json"))
    args = ap.parse_args(argv)

    _, designs, meta = load_sealed(args.sealed)
    specs = [_parse_named_dirs(spec) for spec in args.arm]
    names = [name for name, _ in specs]
    if len(names) != len(set(names)):
        raise AnalysisInputError(f"duplicate arm name in {names}")
    if args.primary not in names:
        raise AnalysisInputError(f"primary arm {args.primary!r} was not supplied")

    validate_generation_config(
        args.sft, policy="sft", training_seed=0, generation_seed=100,
        n=SFT_SAMPLES, score_rf=True, checkpoint="sft_v6c_out")
    for name, dirs in specs:
        if name == args.primary:
            if len(dirs) != 2:
                raise AnalysisInputError("the primary RF arm requires exactly two seeds")
            for seed, directory in enumerate(dirs, 1):
                validate_generation_config(
                    directory, policy=f"rf_s{seed}", training_seed=seed,
                    generation_seed=100 + seed, n=ENDPOINT_SAMPLES,
                    score_rf=True, checkpoint=f"grpo_rf_s{seed}/upd_276")
        elif name == "mlp":
            if len(dirs) not in (1, 2):
                raise AnalysisInputError("the MLP arm requires one or two seeds")
            per_seed_n = ENDPOINT_SAMPLES if len(dirs) == 2 else SFT_SAMPLES
            for seed, directory in enumerate(dirs, 1):
                validate_generation_config(
                    directory, policy=f"mlp_s{seed}", training_seed=seed,
                    generation_seed=100 + seed, n=per_seed_n,
                    score_rf=False, checkpoint=f"grpo_mlp_s{seed}/upd_276")
        elif name == "correctness":
            if len(dirs) != 1:
                raise AnalysisInputError("the correctness arm requires its one frozen seed")
            validate_generation_config(
                dirs[0], policy="correctness_s1", training_seed=1,
                generation_seed=101, n=SFT_SAMPLES, score_rf=False,
                checkpoint="grpo_corr_s1/upd_276")
        else:
            raise AnalysisInputError(f"unknown preregistered arm name: {name}")

    # SFT and the primary arm must be scored by rf_struct as well as Vivado so
    # the endpoint reward-reality check is computed, not entered manually.
    sft = load_arm([args.sft], designs, meta, SFT_SAMPLES, {1},
                   require_reward=True)
    arms: Dict[str, ArmData] = {}
    for name, dirs in specs:
        if name == args.primary:
            expected_n, allowed = ENDPOINT_SAMPLES, {2}
        elif name == "mlp":
            # With both training seeds, each replicate contributes 24 draws.
            # The sole preregistered budget cut permits one MLP training seed;
            # that single policy then receives the same 48-draw arm budget.
            expected_n = ENDPOINT_SAMPLES if len(dirs) == 2 else SFT_SAMPLES
            allowed = {1, 2}
        elif name == "correctness":
            # Amendment 1 fixes one full-budget correctness training seed.  Its
            # evaluation still receives 48 draws/design, equal to every arm.
            expected_n, allowed = SFT_SAMPLES, {1}
        else:
            raise AnalysisInputError(f"unknown preregistered arm name: {name}")
        arms[name] = load_arm(dirs, designs, meta, expected_n, allowed,
                              require_reward=(name == args.primary))
    primary = arms[args.primary]
    if len(primary.seeds) != EXPECTED_RF_SEEDS:
        raise AnalysisInputError("the primary rf_struct arm requires both seeds")

    mid = None
    if args.mid:
        mid_name, mid_dirs = _parse_named_dirs(args.mid)
        if mid_name != args.primary:
            raise AnalysisInputError("--mid must name the primary arm")
        if len(mid_dirs) != 2:
            raise AnalysisInputError("the RF midpoint requires exactly two seeds")
        for seed, directory in enumerate(mid_dirs, 1):
            validate_generation_config(
                directory, policy=f"rf_mid_s{seed}", training_seed=seed,
                generation_seed=100 + seed, n=MID_SAMPLES, score_rf=True,
                checkpoint=f"grpo_rf_s{seed}/upd_138")
        mid = load_arm(mid_dirs, designs, meta, MID_SAMPLES, {2},
                       require_reward=True)

    group_stats = load_group_logs(args.rf_group_log)
    gate = load_mutation_contract(args.mutation_contract,
                                  group_stats["distinct_rtl_candidates"])
    plans = make_bootstrap_plans(designs, meta)
    reports = {name: report_arm(arm, sft, designs, meta, plans)
               for name, arm in arms.items()}
    reward_delta = reward_change(primary, sft, designs, meta)
    late = late_divergence(mid, primary, designs, meta)

    retention = None
    if "mlp" in reports:
        denominator = reports["mlp"]["combined"]["all"]["mean_diff"]
        numerator = reports[args.primary]["combined"]["all"]["mean_diff"]
        if denominator > 0:
            retention = numerator / denominator
    label, why = classify(reports[args.primary], gate, group_stats,
                          reward_delta, late)

    result = {
        "analysis_revision": 3,
        "n_designs": len(designs), "designs": designs,
        "bootstrap": {"n": N_BOOT, "ci": CI, "seed": BOOT_SEED,
                      "strata": "family x regime",
                      "identical_resamples_across_arms": True,
                      "plan_sha256": {k: v.digest for k, v in plans.items()}},
        "sft": sft.combined,
        "arms": {name: arm.combined for name, arm in arms.items()},
        "report": reports,
        "rf_group_diagnostics": group_stats,
        "mutation_contract": gate,
        "endpoint_reward_change": reward_delta,
        "late_divergence": late,
        "retention": retention,
        "high_retention": (None if retention is None
                           else retention >= RETENTION_THRESHOLD),
        "outcome": label, "outcome_why": why,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1)
        f.write("\n")

    print(f"sealed designs analysed: {len(designs)} / {len(designs)}")
    for name, report in reports.items():
        print(f"\n=== {name} ===")
        for scope in ("interp", "extrap", "all"):
            row = report["combined"][scope]
            print(f"  {scope:7s} n={row['n_designs']:2d}  "
                  f"SFT {row['sft_equal']:6.1f} -> {row['arm_equal']:6.1f} MHz  "
                  f"diff {row['mean_diff']:+6.1f} "
                  f"[{row['ci_lo']:+.1f}, {row['ci_hi']:+.1f}]")
        print("  per-seed regime effects:", report["per_seed"])
    print(f"\nreward resolution: {group_stats['resolved_groups']}/"
          f"{group_stats['eligible_groups']} "
          f"({100.0 * group_stats['resolved_fraction']:.1f}%)")
    print(f"mutation/trace gate: {'PASS' if gate['ok'] else 'FAIL'}")
    print(f"\nPREREGISTERED OUTCOME: {label}\n  {why}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AnalysisInputError as exc:
        raise SystemExit(f"analysis input error: {exc}")
