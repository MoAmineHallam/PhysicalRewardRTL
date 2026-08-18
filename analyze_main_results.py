#!/usr/bin/env python3
"""Canonical, fail-closed analysis for the paper's empirical claims.

This is the only script allowed to create headline result tables.  It consumes
the three frozen grpo_v8 evaluation chunks (exactly 30 held-out designs), scores
every original sample at equal cost, and assigns 0 MHz to incorrect samples and
to implementation failures.  It also derives the perfect-selector best-of-N
comparison and the bounded v8 reward-trajectory diagnostic.

Outputs are generated, never hand edited:

  paper/generated/claims.tex
  paper/generated/claims.json
  paper/generated/claim_provenance.md
  paper/generated/table_main.tex
  paper/generated/table_family.tex
  paper/generated/table_bestofn.tex
  paper/generated/table_trajectory.tex
  paper/generated/table_replication.tex
  paper/generated/table_context.tex
  paper/generated/table_ppa.tex
  paper/generated/table_board.tex
  paper/figures/fig_main_verified.{pdf,png}
  paper/figures/fig_mechanism_verified.{pdf,png}
  paper/figures/fig_trajectory_verified.{pdf,png}

Run ``python analyze_main_results.py --check`` in CI or before compiling the
paper.  Check mode recomputes everything and fails if a generated text artifact
is missing or stale.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import pathlib
import re
import sys
from dataclasses import dataclass

import numpy as np


ROOT = pathlib.Path(__file__).resolve().parent
PRIMARY_DIRS = tuple(
    ROOT / "rtl" / name
    for name in (
        "holdout_eval_v8_firfirr",
        "holdout_eval_v8_poly",
        "holdout_eval_v8_iirmed",
    )
)
TRAJECTORY_DIR = ROOT / "rtl" / "traj_v8"
QWEN_DIR = ROOT / "rtl" / "holdout_eval_qwen"
FRONTIER_DIR = ROOT / "rtl" / "frontier_eval"
HLS_RESULT_PATH = ROOT / "rtl" / "hls_baseline" / "hls_results.json"
HLS_LLM_DIR = ROOT / "rtl" / "holdout_eval"
REFLOW_PATH = ROOT / "reflow_attribution.json"
EVAL_SCRIPT = ROOT / "eval_holdout.py"
PPA_SCRIPT = ROOT / "run_ppa.py"
PPA_TCL = ROOT / "ppa_synth.tcl"
VERILOGEVAL_FILES = collections.OrderedDict(
    (
        ("base", ROOT / "passk_base.jsonl"),
        ("sft", ROOT / "passk_sft_v5.jsonl"),
        ("grpo", ROOT / "passk_grpo_v7.jsonl"),
    )
)
SYMMETRIC_BOARD_DIR = ROOT / "rtl" / "holdout_silicon_symmetric"
GENERATED = ROOT / "paper" / "generated"
FIGURES = ROOT / "paper" / "figures"
EXPECTED_DESIGNS = 30
EXPECTED_REGIMES = {"interp": 19, "extrap": 11}
EXPECTED_POLICIES = ("sft", "grpo")
BOOTSTRAP_SEED = 20260817
BOOTSTRAP_REPS = 100_000


@dataclass(frozen=True)
class Candidate:
    module: str
    policy: str
    design: str
    regime: str
    count: int
    n: int
    fmax: float
    compiled: bool
    lut: float | None
    ff: float | None
    dsp: float | None
    bram: float | None
    power_w: float | None
    manifest_source: str
    ppa_source: str


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def line_count(path: pathlib.Path) -> int:
    with path.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def file_span(path: pathlib.Path) -> str:
    return f"{rel(path)}:1-{line_count(path)}"


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def manifest_lines(path: pathlib.Path) -> dict[str, int]:
    out = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith('"') and stripped.endswith((': {', '": {')):
            key = stripped.split('"', 2)[1]
            if "__" in key:
                out[key] = lineno
    return out


def load_eval_dirs(eval_dirs: tuple[pathlib.Path, ...]) -> tuple[list[Candidate], dict]:
    candidates: list[Candidate] = []
    artifacts = []
    seen_modules = set()
    design_owner = {}
    for directory in eval_dirs:
        manifest_path = directory / "fmax_manifest.json"
        ppa_path = directory / "ppa.jsonl"
        summary_path = directory / "holdout_summary.json"
        for path in (manifest_path, ppa_path, summary_path):
            if not path.is_file():
                raise RuntimeError(f"required artifact missing: {rel(path)}")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        mlines = manifest_lines(manifest_path)
        ppa = {}
        plines = {}
        for lineno, line in enumerate(ppa_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            module = row["module"]
            if module in ppa:
                raise RuntimeError(f"duplicate PPA row for {module} in {rel(ppa_path)}")
            ppa[module] = row
            plines[module] = lineno

        for module, info in manifest.items():
            if info["policy"] not in EXPECTED_POLICIES:
                continue
            if module in seen_modules:
                raise RuntimeError(f"module appears in multiple chunks: {module}")
            seen_modules.add(module)
            if module not in ppa:
                raise RuntimeError(
                    f"manifest candidate lacks a PPA result (fail-closed): {module}"
                )
            design = info["design"]
            previous = design_owner.setdefault(design, directory)
            if previous != directory:
                raise RuntimeError(f"design appears in multiple chunks: {design}")
            row = ppa[module]
            compiled = bool(row.get("compiled"))
            fmax = float(row.get("fmax_mhz", 0.0)) if compiled else 0.0
            if not math.isfinite(fmax) or fmax < 0:
                raise RuntimeError(f"invalid Fmax for {module}: {fmax}")
            resources = {}
            for key in ("lut", "ff", "dsp", "bram", "power_w"):
                value = row.get(key) if compiled else None
                if compiled:
                    if value is None:
                        raise RuntimeError(f"compiled PPA row lacks {key}: {module}")
                    value = float(value)
                    if not math.isfinite(value) or value < 0:
                        raise RuntimeError(f"invalid {key} for {module}: {value}")
                resources[key] = value
            candidates.append(
                Candidate(
                    module=module,
                    policy=info["policy"],
                    design=design,
                    regime=info["regime"],
                    count=int(info["count"]),
                    n=int(info["n"]),
                    fmax=fmax,
                    compiled=compiled,
                    lut=resources["lut"],
                    ff=resources["ff"],
                    dsp=resources["dsp"],
                    bram=resources["bram"],
                    power_w=resources["power_w"],
                    manifest_source=f"{rel(manifest_path)}:{mlines.get(module, 1)}",
                    ppa_source=f"{rel(ppa_path)}:{plines[module]}",
                )
            )
        artifacts.extend(
            {
                "path": rel(path),
                "lines": line_count(path),
                "sha256": sha256(path),
            }
            for path in (manifest_path, ppa_path, summary_path)
        )

    return candidates, {"artifacts": artifacts}


def family(design: str) -> str:
    for name in ("firr", "fir", "poly", "iir", "med"):
        if design.startswith(name):
            return name
    raise RuntimeError(f"unknown design family: {design}")


def make_design_rows(candidates: list[Candidate]) -> list[dict]:
    grouped = collections.defaultdict(list)
    for c in candidates:
        grouped[(c.design, c.policy)].append(c)
    designs = sorted({c.design for c in candidates})
    if len(designs) != EXPECTED_DESIGNS:
        raise RuntimeError(f"expected exactly {EXPECTED_DESIGNS} designs, got {len(designs)}")

    regime_counts = collections.Counter()
    rows = []
    for design in designs:
        policy_rows = {}
        regimes = set()
        ns = set()
        for policy in EXPECTED_POLICIES:
            cs = grouped.get((design, policy), [])
            if not cs:
                raise RuntimeError(f"missing {policy} candidates for {design}")
            regimes.update(c.regime for c in cs)
            ns.update(c.n for c in cs)
            n = cs[0].n
            correct = sum(c.count for c in cs)
            if correct > n:
                raise RuntimeError(f"candidate multiplicities exceed n for {policy}/{design}")
            measured_sum = sum(c.count * c.fmax for c in cs)
            implemented = sum(c.count for c in cs if c.compiled)
            if implemented <= 0:
                raise RuntimeError(
                    f"no implemented oracle-correct sample for {policy}/{design}; "
                    "conditional resource diagnostics are undefined")
            conditional_resources = {
                key: sum(c.count * float(getattr(c, key)) for c in cs if c.compiled)
                / implemented
                for key in ("lut", "ff", "dsp", "bram", "power_w")
            }
            sources = sorted({c.manifest_source for c in cs} | {c.ppa_source for c in cs})
            policy_rows[policy] = {
                "n": n,
                "correct": correct,
                "compiled": sum(c.count for c in cs if c.compiled),
                "penalized_fmax": measured_sum / n,
                "conditional_fmax": measured_sum / correct if correct else 0.0,
                "correct_pct": 100.0 * correct / n,
                "conditional_lut": conditional_resources["lut"],
                "conditional_ff": conditional_resources["ff"],
                "conditional_dsp": conditional_resources["dsp"],
                "conditional_bram": conditional_resources["bram"],
                "conditional_power_w": conditional_resources["power_w"],
                "sources": sources,
                "candidates": cs,
            }
        if len(regimes) != 1 or len(ns) != 1:
            raise RuntimeError(f"inconsistent regime or n for {design}: {regimes}, {ns}")
        regime = regimes.pop()
        regime_counts[regime] += 1
        rows.append(
            {
                "design": design,
                "family": family(design),
                "regime": regime,
                "n": ns.pop(),
                "sft": policy_rows["sft"],
                "grpo": policy_rows["grpo"],
            }
        )

    if dict(regime_counts) != EXPECTED_REGIMES:
        raise RuntimeError(
            f"expected regime counts {EXPECTED_REGIMES}, got {dict(regime_counts)}"
        )
    if {r["n"] for r in rows} != {48}:
        raise RuntimeError(f"expected n=48 for every design/policy, got {sorted({r['n'] for r in rows})}")
    return rows


def aggregate(rows: list[dict]) -> dict:
    if not rows:
        raise RuntimeError("cannot aggregate an empty design set")
    out = {"designs": len(rows), "samples_per_design": rows[0]["n"]}
    for policy in EXPECTED_POLICIES:
        p = [r[policy] for r in rows]
        out[policy] = {
            "penalized_fmax": float(np.mean([x["penalized_fmax"] for x in p])),
            "conditional_fmax": sum(x["conditional_fmax"] * x["correct"] for x in p)
            / sum(x["correct"] for x in p),
            "correct_pct": 100.0 * sum(x["correct"] for x in p) / sum(x["n"] for x in p),
        }
    gains = np.asarray(
        [r["grpo"]["penalized_fmax"] - r["sft"]["penalized_fmax"] for r in rows]
    )
    out["gain_mhz"] = float(np.mean(gains))
    out["gain_pct"] = 100.0 * (
        out["grpo"]["penalized_fmax"] / out["sft"]["penalized_fmax"] - 1.0
    )
    out["improved"] = int(np.sum(gains > 1e-12))
    out["tied"] = int(np.sum(np.abs(gains) <= 1e-12))
    out["declined"] = int(np.sum(gains < -1e-12))
    return out


def ppa_summary(rows: list[dict]) -> dict:
    """Equal-design resource diagnostics over implemented, oracle-correct draws.

    Resource means are conditional because assigning zero LUTs or watts to an
    incorrect/failed sample would reward failure. Vivado power is explicitly
    the vectorless estimate; no arbitrary cross-resource area proxy is formed.
    """
    metrics = (
        "conditional_lut", "conditional_ff", "conditional_dsp",
        "conditional_bram", "conditional_power_w",
    )
    out = {
        "conditioning": (
            "resource means condition on oracle-correct, successfully implemented samples; "
            "per-design means are averaged equally"
        )
    }
    for policy in EXPECTED_POLICIES:
        out[policy] = {
            metric: float(np.mean([row[policy][metric] for row in rows]))
            for metric in metrics
        }
    out["grpo_over_sft"] = {
        metric: (out["grpo"][metric] / out["sft"][metric]
                 if out["sft"][metric] != 0 else None)
        for metric in metrics
    }
    out["faster_without_more_lut"] = sum(
        row["grpo"]["penalized_fmax"] > row["sft"]["penalized_fmax"]
        and row["grpo"]["conditional_lut"] <= row["sft"]["conditional_lut"]
        for row in rows
    )
    out["faster_without_more_dsp"] = sum(
        row["grpo"]["penalized_fmax"] > row["sft"]["penalized_fmax"]
        and row["grpo"]["conditional_dsp"] <= row["sft"]["conditional_dsp"]
        for row in rows
    )
    return out


def bootstrap_ci(rows: list[dict], rng: np.random.Generator) -> tuple[float, float]:
    gains = np.asarray(
        [r["grpo"]["penalized_fmax"] - r["sft"]["penalized_fmax"] for r in rows]
    )
    draws = rng.integers(0, len(gains), size=(BOOTSTRAP_REPS, len(gains)))
    boot = gains[draws].mean(axis=1)
    lo, hi = np.quantile(boot, (0.025, 0.975))
    return float(lo), float(hi)


def source_spans(eval_dirs: tuple[pathlib.Path, ...]) -> list[str]:
    return [
        file_span(directory / filename)
        for directory in eval_dirs
        for filename in ("fmax_manifest.json", "ppa.jsonl")
    ]


def load_policy_dataset(
    directory: pathlib.Path,
    policies: tuple[str, ...],
    expected_designs: int,
    expected_n: int,
    expected_families: int,
    expected_regimes: dict[str, int],
    summary_filename: str = "holdout_summary.json",
) -> tuple[list[dict], list[str]]:
    """Load a secondary policy comparison without hiding zero-correct designs.

    The manifest contains only distinct oracle-correct candidates.  The summary
    is therefore the authority for the complete design universe and denominator;
    each manifest multiplicity is checked back against its summary correctness.
    """
    manifest_path = directory / "fmax_manifest.json"
    ppa_path = directory / "ppa.jsonl"
    summary_path = directory / summary_filename
    for path in (manifest_path, ppa_path, summary_path):
        if not path.is_file():
            raise RuntimeError(f"secondary artifact missing: {rel(path)}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    ppa = {}
    for line in ppa_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["module"] in ppa:
            raise RuntimeError(f"duplicate secondary PPA row: {row['module']}")
        ppa[row["module"]] = row

    for policy in policies:
        if policy not in summary:
            raise RuntimeError(f"secondary summary lacks policy {policy}: {rel(summary_path)}")
    design_sets = [set(summary[policy]) for policy in policies]
    if any(designs != design_sets[0] for designs in design_sets[1:]):
        raise RuntimeError(f"secondary policy design sets differ in {rel(summary_path)}")
    designs = sorted(design_sets[0])
    if len(designs) != expected_designs:
        raise RuntimeError(
            f"expected {expected_designs} secondary designs in {rel(directory)}, got {len(designs)}"
        )

    rows = []
    regime_counts = collections.Counter()
    for design in designs:
        policy_rows = {}
        regimes = set()
        for policy in policies:
            sm = summary[policy][design]
            n = int(sm["n"])
            if n != expected_n:
                raise RuntimeError(f"expected n={expected_n} for {policy}/{design}, got {n}")
            regimes.add(sm["regime"])
            candidates = [
                (module, info)
                for module, info in manifest.items()
                if info["policy"] == policy and info["design"] == design
            ]
            if any(module not in ppa for module, _ in candidates):
                missing = [module for module, _ in candidates if module not in ppa]
                raise RuntimeError(f"secondary manifest candidates lack PPA rows: {missing}")
            if any(int(info["n"]) != n or info["regime"] != sm["regime"]
                   for _, info in candidates):
                raise RuntimeError(f"secondary manifest metadata mismatch for {policy}/{design}")
            correct = sum(int(info["count"]) for _, info in candidates)
            summary_correct = float(sm["corr_pct"]) * n / 100.0
            if not math.isclose(correct, summary_correct, abs_tol=1e-6):
                raise RuntimeError(
                    f"summary/manifest correctness mismatch for {policy}/{design}: "
                    f"{summary_correct} versus {correct}"
                )
            weighted = 0.0
            compiled_correct = 0
            for module, info in candidates:
                ppa_row = ppa[module]
                if ppa_row.get("compiled"):
                    fmax = float(ppa_row["fmax_mhz"])
                    if not math.isfinite(fmax) or fmax < 0:
                        raise RuntimeError(f"invalid secondary Fmax for {module}: {fmax}")
                    weighted += int(info["count"]) * fmax
                    compiled_correct += int(info["count"])
            policy_rows[policy] = {
                "n": n,
                "correct": correct,
                "compiled": compiled_correct,
                "penalized_fmax": weighted / n,
                "conditional_fmax": weighted / correct if correct else 0.0,
                "correct_pct": 100.0 * correct / n,
            }
        if len(regimes) != 1:
            raise RuntimeError(f"secondary regime mismatch for {design}: {regimes}")
        regime = regimes.pop()
        regime_counts[regime] += 1
        rows.append({
            "design": design,
            "family": family(design),
            "regime": regime,
            "n": expected_n,
            **policy_rows,
        })

    if dict(regime_counts) != expected_regimes:
        raise RuntimeError(
            f"expected secondary regimes {expected_regimes}, got {dict(regime_counts)}"
        )
    if len({row["family"] for row in rows}) != expected_families:
        raise RuntimeError(
            f"expected {expected_families} secondary families in {rel(directory)}"
        )
    sources = [file_span(manifest_path), file_span(ppa_path), file_span(summary_path)]
    return rows, sources


def aggregate_policy_rows(rows: list[dict], policies: tuple[str, ...]) -> dict:
    if not rows:
        raise RuntimeError("cannot aggregate an empty secondary design set")
    out = {"designs": len(rows), "samples_per_design": rows[0]["n"]}
    for policy in policies:
        total_n = sum(row[policy]["n"] for row in rows)
        total_correct = sum(row[policy]["correct"] for row in rows)
        weighted = sum(row[policy]["penalized_fmax"] * row[policy]["n"] for row in rows)
        out[policy] = {
            "penalized_fmax": float(np.mean([row[policy]["penalized_fmax"] for row in rows])),
            "conditional_fmax": weighted / total_correct if total_correct else 0.0,
            "correct_pct": 100.0 * total_correct / total_n,
        }
    return out


def load_primary_base() -> tuple[dict, list[str]]:
    """Recover the raw-model row over the complete frozen design universe."""
    weighted = 0.0
    correct = 0
    total = 0
    designs = set()
    sources = []
    for directory in PRIMARY_DIRS:
        manifest_path = directory / "fmax_manifest.json"
        ppa_path = directory / "ppa.jsonl"
        summary_path = directory / "holdout_summary.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        ppa = {
            row["module"]: row
            for row in (
                json.loads(line)
                for line in ppa_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        if "base" not in summary:
            raise RuntimeError(f"primary summary lacks base policy: {rel(summary_path)}")
        for design, sm in summary["base"].items():
            if design in designs:
                raise RuntimeError(f"duplicate base design across primary chunks: {design}")
            designs.add(design)
            total += int(sm["n"])
        for module, info in manifest.items():
            if info["policy"] != "base":
                continue
            if module not in ppa:
                raise RuntimeError(f"base manifest candidate lacks PPA row: {module}")
            correct += int(info["count"])
            if ppa[module].get("compiled"):
                weighted += int(info["count"]) * float(ppa[module]["fmax_mhz"])
        summary_correct = sum(
            float(sm["corr_pct"]) * int(sm["n"]) / 100.0
            for sm in summary["base"].values()
        )
        manifest_correct = sum(
            int(info["count"])
            for info in manifest.values()
            if info["policy"] == "base"
        )
        if not math.isclose(summary_correct, manifest_correct, abs_tol=1e-6):
            raise RuntimeError(f"base summary/manifest mismatch in {rel(directory)}")
        sources.extend([file_span(manifest_path), file_span(ppa_path), file_span(summary_path)])
    if len(designs) != EXPECTED_DESIGNS or total != EXPECTED_DESIGNS * 48:
        raise RuntimeError(f"incomplete primary base universe: {len(designs)} designs, n={total}")
    return {
        "designs": len(designs),
        "total": total,
        "correct": correct,
        "correct_pct": 100.0 * correct / total,
        "penalized_fmax": weighted / total,
        "conditional_fmax": weighted / correct if correct else 0.0,
    }, sources


def mechanism_summary(rows: list[dict]) -> dict:
    out = {"overall": {}, "families": {}}
    for label, selected in [("overall", rows)] + [
        (fam, [row for row in rows if row["family"] == fam])
        for fam in ("fir", "firr", "poly", "iir", "med")
    ]:
        entry = {}
        for policy in EXPECTED_POLICIES:
            dominant = [
                max(candidate.count for candidate in row[policy]["candidates"]) / row["n"]
                for row in selected
            ]
            effective = []
            for row in selected:
                counts = np.asarray(
                    [candidate.count for candidate in row[policy]["candidates"]], dtype=float
                )
                probabilities = counts / counts.sum()
                effective.append(float(1.0 / np.sum(probabilities ** 2)))
            entry[policy] = {
                "dominant_mass_pct": 100.0 * float(np.mean(dominant)),
                "effective_correct_implementations": float(np.mean(effective)),
                "unique_correct_implementations": float(np.mean([
                    len(row[policy]["candidates"]) for row in selected
                ])),
            }
        if label == "overall":
            out["overall"] = entry
        else:
            out["families"][label] = entry
    out["sft_support_at_or_above_grpo_conditional"] = sum(
        max(candidate.fmax for candidate in row["sft"]["candidates"])
        >= row["grpo"]["conditional_fmax"]
        for row in rows
    )
    return out


def load_verilogeval() -> tuple[dict, list[str]]:
    def pass_at_k(by_problem: dict[str, list[bool]], k: int) -> float:
        total = 0.0
        for passes in by_problem.values():
            n, correct = len(passes), sum(passes)
            total += (
                1.0
                if n - correct < k
                else 1.0 - math.comb(n - correct, k) / math.comb(n, k)
            )
        return 100.0 * total / len(by_problem)

    out = {}
    sources = []
    for policy, path in VERILOGEVAL_FILES.items():
        if not path.is_file():
            raise RuntimeError(f"VerilogEval artifact missing: {rel(path)}")
        by_problem = collections.defaultdict(list)
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append(row)
            by_problem[row["problem"]].append(row["status"] == "PASS")
        if len(by_problem) != 156 or {len(v) for v in by_problem.values()} != {10}:
            raise RuntimeError(f"unexpected VerilogEval shape for {policy}: {len(by_problem)}")
        out[policy] = {
            "problems": len(by_problem),
            "samples_per_problem": 10,
            "pass_at_one": pass_at_k(by_problem, 1),
            "pass_at_five": pass_at_k(by_problem, 5),
            "pass_at_ten": pass_at_k(by_problem, 10),
            "compile_fail_pct": 100.0 * sum(
                row["status"] == "compile_fail" for row in rows
            ) / len(rows),
        }
        sources.append(file_span(path))
    return out, sources


def load_hls_context() -> tuple[dict, list[str]]:
    """Validate the compact HLS measurement artifact and selected RTL column."""
    if not HLS_RESULT_PATH.is_file():
        raise RuntimeError(f"HLS result artifact missing: {rel(HLS_RESULT_PATH)}")
    table = json.loads(HLS_RESULT_PATH.read_text(encoding="utf-8"))
    if len(table) != 22:
        raise RuntimeError(f"expected 22 HLS design rows, got {len(table)}")

    llm_manifest_path = HLS_LLM_DIR / "fmax_manifest.json"
    llm_ppa_path = HLS_LLM_DIR / "ppa.jsonl"
    llm_manifest = json.loads(llm_manifest_path.read_text(encoding="utf-8"))
    llm_ppa = {
        row["module"]: row
        for row in (
            json.loads(line)
            for line in llm_ppa_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    expert_ratios = []
    naive_ratios = []
    valid_designs = []
    for design, row in table.items():
        grpo_candidates = [
            module
            for module, info in llm_manifest.items()
            if info["policy"] == "grpo" and info["design"] == design
            and module in llm_ppa and llm_ppa[module].get("compiled")
        ]
        expected_top = max(float(llm_ppa[module]["fmax_mhz"]) for module in grpo_candidates)
        if not math.isclose(float(row["grpo_top"]), expected_top, rel_tol=0, abs_tol=1e-9):
            raise RuntimeError(f"HLS selected GRPO column is stale for {design}")
        expert = row["hls_pragma"]
        naive = row["hls_nopragma"]
        if expert["fmax"] is not None and expert["ii"] is not None:
            throughput = float(expert["fmax"]) / int(expert["ii"])
            if not math.isclose(throughput, float(row["thr_pragma"]), abs_tol=1e-9):
                raise RuntimeError(f"HLS expert throughput mismatch for {design}")
            expert_ratios.append(expected_top / throughput)
            valid_designs.append(design)
        if naive["fmax"] is not None and naive["ii"] is not None:
            throughput = float(naive["fmax"]) / int(naive["ii"])
            if not math.isclose(throughput, float(row["thr_nopragma"]), abs_tol=1e-9):
                raise RuntimeError(f"HLS naive throughput mismatch for {design}")
            naive_ratios.append(expected_top / throughput)
    if len(valid_designs) != 19 or len(naive_ratios) != 19:
        raise RuntimeError(
            f"expected 19 implemented HLS comparisons, got {len(valid_designs)}"
        )
    return {
        "designs": valid_designs,
        "selected_grpo_over_expert_geomean": float(math.prod(expert_ratios) ** (1 / len(expert_ratios))),
        "selected_grpo_over_naive_geomean": float(math.prod(naive_ratios) ** (1 / len(naive_ratios))),
        "selected_grpo_over_naive_minimum": min(naive_ratios),
        "selected_grpo_over_naive_maximum": max(naive_ratios),
    }, [file_span(HLS_RESULT_PATH), file_span(llm_manifest_path), file_span(llm_ppa_path)]


def load_reflow_diagnostic() -> tuple[dict, list[str]]:
    if not REFLOW_PATH.is_file():
        raise RuntimeError(f"reflow attribution artifact missing: {rel(REFLOW_PATH)}")
    data = json.loads(REFLOW_PATH.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    if not {"s300", "s400", "_attribution"}.issubset(summary):
        raise RuntimeError("reflow attribution lacks late checkpoints")
    if data.get("token_identical_pairs") != []:
        raise RuntimeError("reflow null-result expectation changed")
    return data, [file_span(REFLOW_PATH)]


def load_protocol_config() -> tuple[dict, list[str]]:
    for path in (EVAL_SCRIPT, PPA_SCRIPT, PPA_TCL):
        if not path.is_file():
            raise RuntimeError(f"protocol source missing: {rel(path)}")
    eval_text = EVAL_SCRIPT.read_text(encoding="utf-8")
    ppa_text = PPA_SCRIPT.read_text(encoding="utf-8")
    tcl_text = PPA_TCL.read_text(encoding="utf-8")
    seed_match = re.search(r"EVAL_SEEDS\s*=\s*\(([^)]*)\)", eval_text)
    vectors_match = re.search(
        r'add_argument\("--n-stim"[^\n]*\n\s*help=.*?default=(\d+)', eval_text, re.S
    )
    if vectors_match is None:
        vectors_match = re.search(
            r'add_argument\("--n-stim"[^)]*default=(\d+)', eval_text, re.S
        )
    period_match = re.search(
        r'add_argument\("--period"[^)]*default=([\d.]+)', ppa_text, re.S
    )
    part_match = re.search(r"^set\s+part\s+(\S+)", tcl_text, re.M)
    if not all((seed_match, vectors_match, period_match, part_match)):
        raise RuntimeError("could not recover frozen evaluation configuration from source")
    seeds = tuple(int(piece.strip()) for piece in seed_match.group(1).split(",") if piece.strip())
    return {
        "oracle_streams": len(seeds),
        "vectors_per_stream": int(vectors_match.group(1)),
        "target_period_ns": float(period_match.group(1)),
        "target_part": part_match.group(1),
    }, [file_span(EVAL_SCRIPT), file_span(PPA_SCRIPT), file_span(PPA_TCL)]


def e_best_of_n(candidates: list[Candidate], n_total: int, n_draws: float) -> float:
    counts = collections.defaultdict(int)
    counts[0.0] = n_total - sum(c.count for c in candidates)
    for c in candidates:
        counts[c.fmax] += c.count
    if counts[0.0] < 0:
        raise RuntimeError("candidate counts exceed sample count")
    cumulative = 0.0
    expectation = 0.0
    for fmax, count in sorted(counts.items()):
        lower = (cumulative / n_total) ** n_draws
        cumulative += count
        expectation += fmax * ((cumulative / n_total) ** n_draws - lower)
    return expectation


def bestof_summary(rows: list[dict]) -> dict:
    out = {}
    for regime in ("interp", "extrap"):
        selected = [r for r in rows if r["regime"] == regime]
        curve = {}
        for n_draws in (1, 8, 16, 32, 48):
            curve[n_draws] = float(
                np.mean(
                    [e_best_of_n(r["sft"]["candidates"], r["n"], n_draws) for r in selected]
                )
            )
        grpo_one = float(
            np.mean([e_best_of_n(r["grpo"]["candidates"], r["n"], 1) for r in selected])
        )
        lo, hi = 1.0, 512.0
        if curve[1] < grpo_one:
            for _ in range(80):
                mid = (lo + hi) / 2.0
                value = float(
                    np.mean(
                        [e_best_of_n(r["sft"]["candidates"], r["n"], mid) for r in selected]
                    )
                )
                if value < grpo_one:
                    lo = mid
                else:
                    hi = mid
        out[regime] = {
            "sft": curve,
            "grpo_one": grpo_one,
            "equivalent_sft_draws": (lo + hi) / 2.0,
        }
    return out


def load_trajectory() -> tuple[list[dict], list[str]]:
    directory = TRAJECTORY_DIR
    manifest_path = directory / "fmax_manifest.json"
    ppa_path = directory / "ppa.jsonl"
    summary_path = directory / "holdout_summary.json"
    for path in (manifest_path, ppa_path, summary_path):
        if not path.is_file():
            raise RuntimeError(f"trajectory artifact missing: {rel(path)}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    ppa = {}
    for line in ppa_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            ppa[row["module"]] = row
    steps = (("step0", 0), ("s100", 100), ("s200", 200), ("s300", 300), ("s400", 400))
    rows = []
    for policy, step in steps:
        records = [i for i in manifest.values() if i["policy"] == policy]
        if not records or policy not in summary:
            raise RuntimeError(f"trajectory checkpoint missing: {policy}")
        designs = summary[policy]
        # Count one common sampling budget for each design.
        total_n = sum(max(i["n"] for i in records if i["design"] == design) for design in designs)
        correct = sum(i["count"] for i in records)
        weighted = 0.0
        compiled_correct = 0
        for module, info in manifest.items():
            if info["policy"] != policy:
                continue
            row = ppa.get(module)
            if row is None:
                raise RuntimeError(f"trajectory manifest row lacks PPA: {module}")
            if row.get("compiled"):
                weighted += float(row["fmax_mhz"]) * info["count"]
                compiled_correct += info["count"]
        rows.append(
            {
                "policy": policy,
                "step": step,
                "proxy_fmax": float(np.mean([v["mean_surr_fmax"] for v in designs.values()])),
                "penalized_fmax": weighted / total_n,
                "conditional_fmax": weighted / correct if correct else 0.0,
                "correct_pct": 100.0 * correct / total_n,
                "compiled_correct": compiled_correct,
                "correct": correct,
                "total": total_n,
            }
        )
    return rows, [file_span(manifest_path), file_span(ppa_path), file_span(summary_path)]


class Claims:
    def __init__(self):
        self.data = collections.OrderedDict()

    def add(self, key: str, value, display: str, unit: str, method: str, sources: list[str]):
        if not key.isalpha():
            raise RuntimeError(f"claim IDs must contain letters only: {key}")
        if key in self.data:
            raise RuntimeError(f"duplicate claim: {key}")
        self.data[key] = {
            "value": value,
            "display": display,
            "unit": unit,
            "method": method,
            "sources": sorted(set(sources)),
        }


def fmt(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}"


def build_claims(rows: list[dict], bestof: dict, trajectory: list[dict],
                 primary_sources: list[str], trajectory_sources: list[str]) -> tuple[Claims, dict]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    groups = {
        "Interp": [r for r in rows if r["regime"] == "interp"],
        "Extrap": [r for r in rows if r["regime"] == "extrap"],
        "Overall": rows,
    }
    aggregates = {}
    cis = {}
    claims = Claims()

    claims.add("DesignCount", len(rows), str(len(rows)), "designs",
               "Count distinct design names after strict three-chunk merge.", primary_sources)
    claims.add("InterpDesignCount", len(groups["Interp"]), str(len(groups["Interp"])), "designs",
               "Count designs whose frozen manifest regime is interp.", primary_sources)
    claims.add("ExtrapDesignCount", len(groups["Extrap"]), str(len(groups["Extrap"])), "designs",
               "Count designs whose frozen manifest regime is extrap.", primary_sources)
    claims.add("SamplesPerDesign", rows[0]["n"], str(rows[0]["n"]), "samples/policy/design",
               "Assert the common n field in every manifest policy/design group.", primary_sources)
    claims.add("FamilyCount", len({r["family"] for r in rows}), str(len({r["family"] for r in rows})),
               "families", "Count family prefixes in the frozen design set.", primary_sources)

    for label, selected in groups.items():
        a = aggregate(selected)
        ci = bootstrap_ci(selected, rng)
        aggregates[label.lower()] = a
        cis[label.lower()] = ci
        # Aggregate claims cite the complete frozen manifest/PPA spans.  Keeping
        # one span per artifact is exact, human-readable provenance; enumerating
        # hundreds of contributing JSONL rows obscures rather than improves it.
        sources = primary_sources
        for policy, ptitle in (("sft", "Sft"), ("grpo", "Grpo")):
            p = a[policy]
            claims.add(f"{label}{ptitle}Penalized", p["penalized_fmax"], fmt(p["penalized_fmax"]),
                       "MHz", "Mean over designs of sum(count * real post-route Fmax) / n; all unrepresented incorrect samples and implementation failures score zero.", sources)
            claims.add(f"{label}{ptitle}Conditional", p["conditional_fmax"], fmt(p["conditional_fmax"]),
                       "MHz", "Count-weighted real post-route Fmax divided by oracle-correct sample count; implementation failures remain zero.", sources)
            claims.add(f"{label}{ptitle}Correctness", p["correct_pct"], fmt(p["correct_pct"]),
                       "percent", "Oracle-correct sample multiplicity divided by total original samples.", sources)
        claims.add(f"{label}Gain", a["gain_mhz"], fmt(a["gain_mhz"]), "MHz",
                   "Mean paired per-design difference in penalized equal-sample Fmax.", sources)
        claims.add(f"{label}RelativeGain", a["gain_pct"], fmt(a["gain_pct"], 0), "percent",
                   "Relative change of aggregate penalized Fmax: 100 * (GRPO / SFT - 1).", sources)
        claims.add(f"{label}CiLow", ci[0], fmt(ci[0]), "MHz",
                   f"Percentile paired-design bootstrap, seed {BOOTSTRAP_SEED}, {BOOTSTRAP_REPS} resamples.", sources)
        claims.add(f"{label}CiHigh", ci[1], fmt(ci[1]), "MHz",
                   f"Percentile paired-design bootstrap, seed {BOOTSTRAP_SEED}, {BOOTSTRAP_REPS} resamples.", sources)
        claims.add(f"{label}Improved", a["improved"], str(a["improved"]), "designs",
                   "Count designs with strictly positive paired penalized-Fmax difference.", sources)
        claims.add(f"{label}Declined", a["declined"], str(a["declined"]), "designs",
                   "Count designs with strictly negative paired penalized-Fmax difference.", sources)

    ppa = ppa_summary(rows)
    ppa_specs = (
        ("Lut", "conditional_lut", "LUTs", 1,
         "Per-design mean LUT count, multiplicity-weighted among oracle-correct candidates with successful implementation."),
        ("Ff", "conditional_ff", "flip-flops", 1,
         "Per-design mean flip-flop count, multiplicity-weighted among oracle-correct candidates with successful implementation."),
        ("Dsp", "conditional_dsp", "DSP blocks", 2,
         "Per-design mean DSP count, multiplicity-weighted among oracle-correct candidates with successful implementation."),
        ("Power", "conditional_power_w", "W", 3,
         "Per-design mean Vivado vectorless power estimate, multiplicity-weighted among oracle-correct candidates with successful implementation."),
    )
    for label, metric, unit, digits, method in ppa_specs:
        for policy, policy_name in (("sft", "Sft"), ("grpo", "Grpo")):
            value = ppa[policy][metric]
            claims.add(f"Ppa{policy_name}{label}", value, fmt(value, digits),
                       unit, method, primary_sources)
        ratio = ppa["grpo_over_sft"][metric]
        if ratio is not None:
            claims.add(f"Ppa{label}Ratio", ratio, fmt(ratio, 2), "ratio",
                       f"GRPO divided by SFT for the generated {metric} diagnostic.",
                       primary_sources)
    claims.add("PpaFasterNoMoreLut", ppa["faster_without_more_lut"],
               str(ppa["faster_without_more_lut"]), "designs",
               "Count designs with higher GRPO penalized Fmax and no increase in conditional mean LUT count.",
               primary_sources)
    claims.add("PpaFasterNoMoreDsp", ppa["faster_without_more_dsp"],
               str(ppa["faster_without_more_dsp"]), "designs",
               "Count designs with higher GRPO penalized Fmax and no increase in conditional mean DSP count.",
               primary_sources)

    for reg, prefix in (("interp", "Interp"), ("extrap", "Extrap")):
        b = bestof[reg]
        for n, word in ((1, "One"), (8, "Eight"), (16, "Sixteen"),
                        (32, "Thirtytwo"), (48, "Fortyeight")):
            claims.add(f"{prefix}SftBestof{word}", b["sft"][n], fmt(b["sft"][n]), "MHz",
                       f"Mean exact empirical expected maximum of {n} i.i.d. SFT draws with a perfect selector; incorrect samples score zero.", primary_sources)
        claims.add(f"{prefix}GrpoOne", b["grpo_one"], fmt(b["grpo_one"]), "MHz",
                   "Mean expected penalized Fmax of one GRPO draw.", primary_sources)
        claims.add(f"{prefix}EquivalentDraws", b["equivalent_sft_draws"],
                   fmt(b["equivalent_sft_draws"], 0), "SFT draws",
                   "Continuous-N solution where the empirical perfect-selector SFT curve reaches one GRPO draw.", primary_sources)

    trajectory_names = ("Start", "Early", "Middle", "Late", "Final")
    for name, row in zip(trajectory_names, trajectory):
        claims.add(f"Trajectory{name}Step", row["step"], str(row["step"]), "training steps",
                   "Checkpoint identifier in the trajectory manifest.", trajectory_sources)
        for field, suffix, unit in (
            ("proxy_fmax", "Proxy", "MHz"),
            ("penalized_fmax", "Penalized", "MHz"),
            ("conditional_fmax", "Conditional", "MHz"),
            ("correct_pct", "Correctness", "percent"),
        ):
            claims.add(f"Trajectory{name}{suffix}", row[field], fmt(row[field]), unit,
                       "Twelve-design FIR/FIRR trajectory diagnostic; proxy from summary, measured values from Vivado PPA joined through manifest multiplicities.", trajectory_sources)

    result = {
        "schema": 1,
        "primary_endpoint": "mean per-design equal-sample Fmax; incorrect and implementation-failed samples score 0 MHz",
        "designs": [
            {
                "design": r["design"],
                "family": r["family"],
                "regime": r["regime"],
                "n": r["n"],
                "sft": {k: v for k, v in r["sft"].items() if k not in ("candidates", "sources")},
                "grpo": {k: v for k, v in r["grpo"].items() if k not in ("candidates", "sources")},
            }
            for r in rows
        ],
        "aggregates": aggregates,
        "bootstrap_ci": cis,
        "ppa": ppa,
        "bestof": bestof,
        "trajectory": trajectory,
    }
    return claims, result


def add_secondary_claims(
    claims: Claims,
    result: dict,
    primary_sources: list[str],
    base: dict,
    base_sources: list[str],
    mechanism: dict,
    qwen_rows: list[dict],
    qwen_sources: list[str],
    frontier_rows: list[dict],
    frontier_sources: list[str],
    verilogeval: dict,
    verilogeval_sources: list[str],
    hls: dict,
    hls_sources: list[str],
    reflow: dict,
    reflow_sources: list[str],
    protocol: dict,
    protocol_sources: list[str],
) -> None:
    claims.add("BaseCorrectness", base["correct_pct"], fmt(base["correct_pct"]),
               "percent", "Oracle-correct raw-model samples divided by the complete frozen sample universe.",
               base_sources)
    claims.add("BasePenalized", base["penalized_fmax"], fmt(base["penalized_fmax"]),
               "MHz", "Real post-route Fmax over the complete raw-model sample universe; incorrect and implementation-failed samples score zero.",
               base_sources)

    overall_mechanism = mechanism["overall"]
    claims.add("MechanismSftDominantMass",
               overall_mechanism["sft"]["dominant_mass_pct"],
               fmt(overall_mechanism["sft"]["dominant_mass_pct"]), "percent",
               "Mean across designs of the all-sample mass assigned to the most frequent distinct oracle-correct SFT implementation.",
               primary_sources)
    claims.add("MechanismGrpoDominantMass",
               overall_mechanism["grpo"]["dominant_mass_pct"],
               fmt(overall_mechanism["grpo"]["dominant_mass_pct"]), "percent",
               "Mean across designs of the all-sample mass assigned to the most frequent distinct oracle-correct GRPO implementation.",
               primary_sources)
    claims.add("MechanismSftEffective",
               overall_mechanism["sft"]["effective_correct_implementations"],
               fmt(overall_mechanism["sft"]["effective_correct_implementations"], 2),
               "effective implementations",
               "Mean inverse-Simpson effective count over distinct oracle-correct SFT implementations, conditional on correctness.",
               primary_sources)
    claims.add("MechanismGrpoEffective",
               overall_mechanism["grpo"]["effective_correct_implementations"],
               fmt(overall_mechanism["grpo"]["effective_correct_implementations"], 2),
               "effective implementations",
               "Mean inverse-Simpson effective count over distinct oracle-correct GRPO implementations, conditional on correctness.",
               primary_sources)
    claims.add("MechanismSupportCount",
               mechanism["sft_support_at_or_above_grpo_conditional"],
               str(mechanism["sft_support_at_or_above_grpo_conditional"]), "designs",
               "Count designs where at least one measured SFT candidate reaches or exceeds the GRPO conditional mean Fmax.",
               primary_sources)
    claims.add("MechanismMedianSftDominantMass",
               mechanism["families"]["med"]["sft"]["dominant_mass_pct"],
               fmt(mechanism["families"]["med"]["sft"]["dominant_mass_pct"]),
               "percent", "Median-family version of the dominant distinct-implementation mass diagnostic.",
               primary_sources)
    claims.add("MechanismMedianGrpoDominantMass",
               mechanism["families"]["med"]["grpo"]["dominant_mass_pct"],
               fmt(mechanism["families"]["med"]["grpo"]["dominant_mass_pct"]),
               "percent", "Median-family version of the dominant distinct-implementation mass diagnostic.",
               primary_sources)

    qwen_groups = collections.OrderedDict((
        ("Interp", [row for row in qwen_rows if row["regime"] == "interp"]),
        ("Extrap", [row for row in qwen_rows if row["regime"] == "extrap"]),
        ("Overall", qwen_rows),
    ))
    qwen_result = {"regimes": {}, "bootstrap_seed": BOOTSTRAP_SEED,
                   "bootstrap_replicates": BOOTSTRAP_REPS}
    for label, selected in qwen_groups.items():
        aggregate_row = aggregate(selected)
        ci = bootstrap_ci(selected, np.random.default_rng(BOOTSTRAP_SEED))
        qwen_result["regimes"][label.lower()] = {"aggregate": aggregate_row, "ci": ci}
        for policy, policy_name in (("sft", "Sft"), ("grpo", "Grpo")):
            claims.add(f"Qwen{label}{policy_name}Penalized",
                       aggregate_row[policy]["penalized_fmax"],
                       fmt(aggregate_row[policy]["penalized_fmax"]), "MHz",
                       "Mean per-design equal-sample post-route Fmax in the second-backbone replication; incorrect and implementation-failed samples score zero.",
                       qwen_sources)
            claims.add(f"Qwen{label}{policy_name}Correctness",
                       aggregate_row[policy]["correct_pct"],
                       fmt(aggregate_row[policy]["correct_pct"]), "percent",
                       "Oracle-correct sample multiplicity divided by the full second-backbone sample budget.",
                       qwen_sources)
        claims.add(f"Qwen{label}Gain", aggregate_row["gain_mhz"],
                   fmt(aggregate_row["gain_mhz"]), "MHz",
                   "Mean paired per-design penalized-Fmax difference in the second-backbone replication.",
                   qwen_sources)
        claims.add(f"Qwen{label}Improved", aggregate_row["improved"],
                   str(aggregate_row["improved"]), "designs",
                   "Count second-backbone designs with a positive paired penalized-Fmax difference.",
                   qwen_sources)
        claims.add(f"Qwen{label}CiLow", ci[0], fmt(ci[0]), "MHz",
                   f"Percentile paired-design bootstrap for the second backbone, seed {BOOTSTRAP_SEED}, {BOOTSTRAP_REPS} resamples.",
                   qwen_sources)
        claims.add(f"Qwen{label}CiHigh", ci[1], fmt(ci[1]), "MHz",
                   f"Percentile paired-design bootstrap for the second backbone, seed {BOOTSTRAP_SEED}, {BOOTSTRAP_REPS} resamples.",
                   qwen_sources)
    claims.add("QwenDesignCount", len(qwen_rows), str(len(qwen_rows)), "designs",
               "Count designs in the committed second-backbone evaluation.", qwen_sources)
    claims.add("QwenInterpDesignCount", len(qwen_groups["Interp"]),
               str(len(qwen_groups["Interp"])), "designs",
               "Count interpolation designs in the second-backbone evaluation.", qwen_sources)
    claims.add("QwenExtrapDesignCount", len(qwen_groups["Extrap"]),
               str(len(qwen_groups["Extrap"])), "designs",
               "Count extrapolation designs in the second-backbone evaluation.", qwen_sources)
    claims.add("QwenFamilyCount", len({row["family"] for row in qwen_rows}),
               str(len({row["family"] for row in qwen_rows})), "families",
               "Count circuit families in the second-backbone evaluation.", qwen_sources)
    claims.add("QwenSamplesPerDesign", qwen_rows[0]["n"], str(qwen_rows[0]["n"]),
               "samples/policy/design", "Common second-backbone sampling budget.", qwen_sources)

    frontier_aggregate = aggregate_policy_rows(frontier_rows, ("apiplain", "apifast"))
    for policy, label in (("apiplain", "Plain"), ("apifast", "Fast")):
        values = frontier_aggregate[policy]
        claims.add(f"Frontier{label}Penalized", values["penalized_fmax"],
                   fmt(values["penalized_fmax"]), "MHz",
                   "Mean per-design equal-sample post-route Fmax for the stored API arm; incorrect and implementation-failed samples score zero.",
                   frontier_sources)
        claims.add(f"Frontier{label}Conditional", values["conditional_fmax"],
                   fmt(values["conditional_fmax"]), "MHz",
                   "Count-weighted post-route Fmax conditional on oracle correctness for the stored API arm.",
                   frontier_sources)
        claims.add(f"Frontier{label}Correctness", values["correct_pct"],
                   fmt(values["correct_pct"]), "percent",
                   "Oracle-correct sample multiplicity divided by the complete API-arm budget.",
                   frontier_sources)
    claims.add("FrontierSamplesPerDesign", frontier_rows[0]["n"],
               str(frontier_rows[0]["n"]), "samples/arm/design",
               "Common sampling budget for each stored API prompt arm.", frontier_sources)

    claims.add("VerilogProblemCount", verilogeval["sft"]["problems"],
               str(verilogeval["sft"]["problems"]), "problems",
               "Count distinct VerilogEval problems in every stored policy file.",
               verilogeval_sources)
    claims.add("VerilogSamplesPerProblem", verilogeval["sft"]["samples_per_problem"],
               str(verilogeval["sft"]["samples_per_problem"]), "samples/problem",
               "Common VerilogEval sample count per problem and policy.", verilogeval_sources)
    for policy, label in (("base", "Base"), ("sft", "Sft"), ("grpo", "Grpo")):
        claims.add(f"Verilog{label}Passone", verilogeval[policy]["pass_at_one"],
                   fmt(verilogeval[policy]["pass_at_one"]), "percent",
                   "Unbiased VerilogEval pass-at-one estimator from stored per-sample verdicts.",
                   verilogeval_sources)
        claims.add(f"Verilog{label}CompileFail", verilogeval[policy]["compile_fail_pct"],
                   fmt(verilogeval[policy]["compile_fail_pct"]), "percent",
                   "Compile-failure fraction in stored VerilogEval samples.",
                   verilogeval_sources)
    verilog_delta = verilogeval["grpo"]["pass_at_one"] - verilogeval["sft"]["pass_at_one"]
    claims.add("VerilogRlDelta", verilog_delta, fmt(verilog_delta), "percentage points",
               "GRPO pass-at-one minus SFT pass-at-one on the same VerilogEval problems.",
               verilogeval_sources)

    claims.add("HlsDesignCount", len(hls["designs"]), str(len(hls["designs"])),
               "designs", "Count designs with both post-implementation expert-HLS and selected-GRPO throughput.",
               hls_sources)
    claims.add("HlsExpertGeomean", hls["selected_grpo_over_expert_geomean"],
               fmt(hls["selected_grpo_over_expert_geomean"], 2), "ratio",
               "Geometric mean of selected fastest GRPO candidate throughput divided by pragma-optimized HLS throughput.",
               hls_sources)
    claims.add("HlsNaiveGeomean", hls["selected_grpo_over_naive_geomean"],
               fmt(hls["selected_grpo_over_naive_geomean"], 1), "ratio",
               "Geometric mean of selected fastest GRPO candidate throughput divided by no-pragma HLS throughput.",
               hls_sources)
    claims.add("HlsNaiveMinimum", hls["selected_grpo_over_naive_minimum"],
               fmt(hls["selected_grpo_over_naive_minimum"], 1), "ratio",
               "Minimum selected-GRPO/no-pragma-HLS throughput ratio.", hls_sources)
    claims.add("HlsNaiveMaximum", hls["selected_grpo_over_naive_maximum"],
               fmt(hls["selected_grpo_over_naive_maximum"], 1), "ratio",
               "Maximum selected-GRPO/no-pragma-HLS throughput ratio.", hls_sources)

    late = reflow["summary"]["s300"]
    final = reflow["summary"]["s400"]
    attribution = reflow["summary"]["_attribution"]
    for name, row in (("Late", late), ("Final", final)):
        claims.add(f"Reflow{name}RawNonblocking", row["nb_raw"],
                   fmt(row["nb_raw"]), "line-initial assignments",
                   "Multiplicity-weighted deployed line-initial nonblocking-assignment feature on stored trajectory candidates.",
                   reflow_sources)
        claims.add(f"Reflow{name}CanonicalNonblocking", row["nb_canon"],
                   fmt(row["nb_canon"]), "canonical assignments",
                   "Multiplicity-weighted nonblocking-assignment feature after layout canonicalization.",
                   reflow_sources)
        claims.add(f"Reflow{name}Tokens", row["tokens"], fmt(row["tokens"]),
                   "tokens", "Multiplicity-weighted layout-blind token count on stored trajectory candidates.",
                   reflow_sources)
    claims.add("ReflowRemoved", attribution["pct_removed"],
               fmt(attribution["pct_removed"]), "percent",
               "Share of the late raw proxy jump removed by the diagnostic layout canonicalization; canonical scores are clamp-saturated and this is not a repaired reward.",
               reflow_sources)
    claims.add("ReflowTokenPairCount", len(reflow["token_identical_pairs"]),
               str(len(reflow["token_identical_pairs"])), "pairs",
               "Token-identical cross-checkpoint candidate pairs found by the committed diagnostic.",
               reflow_sources)

    claims.add("EvalOracleStreams", protocol["oracle_streams"],
               str(protocol["oracle_streams"]), "stimulus streams",
               "Count disjoint held-out oracle stimulus seeds in the evaluation source.",
               protocol_sources)
    claims.add("EvalVectorsPerStream", protocol["vectors_per_stream"],
               str(protocol["vectors_per_stream"]), "vectors/stream",
               "Default held-out vector count per oracle stimulus stream in the evaluation source.",
               protocol_sources)
    claims.add("TargetPeriod", protocol["target_period_ns"],
               fmt(protocol["target_period_ns"]), "ns",
               "Requested clock period in the committed physical-evaluation driver.",
               protocol_sources)
    claims.add("TargetPart", protocol["target_part"], protocol["target_part"],
               "FPGA part", "Target FPGA part in the committed post-route Tcl flow.",
               protocol_sources)

    result["base"] = base
    result["mechanism"] = mechanism
    result["qwen_replication"] = qwen_result
    result["frontier_context"] = frontier_aggregate
    result["verilogeval"] = verilogeval
    result["hls_context"] = hls
    result["reflow_diagnostic"] = reflow
    result["protocol"] = protocol


def tex_claims(claims: Claims) -> str:
    lines = [
        "% AUTO-GENERATED by analyze_main_results.py. DO NOT EDIT.",
        "% Every value below is backed by paper/generated/claims.json.",
        r"\providecommand{\claim}[1]{\csname Claim#1\endcsname}",
        "",
    ]
    for key, claim in claims.data.items():
        lines.append(f"% CLAIM {key}: {claim['unit']}; {claim['method']}")
        for source in claim["sources"]:
            lines.append(f"% SOURCE {source}")
        display = claim["display"].replace("%", r"\%")
        lines.append(rf"\expandafter\def\csname Claim{key}\endcsname{{{display}}}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def table_main() -> str:
    return r"""% AUTO-GENERATED by analyze_main_results.py. DO NOT EDIT.
\begin{table}[t]
\centering
\caption{Primary equal-sample endpoint. Incorrect samples and implementation
failures score zero. Intervals are paired-design bootstrap intervals.}
\label{tab:main-verified}
\small
\begin{tabular}{lrrrr}
\toprule
Regime & SFT & GRPO & Gain [CI] & Improved \\
\midrule
Interpolation & \claim{InterpSftPenalized} & \claim{InterpGrpoPenalized} &
\claim{InterpGain} [\claim{InterpCiLow}, \claim{InterpCiHigh}] &
\claim{InterpImproved}/\claim{InterpDesignCount} \\
Extrapolation & \claim{ExtrapSftPenalized} & \claim{ExtrapGrpoPenalized} &
\claim{ExtrapGain} [\claim{ExtrapCiLow}, \claim{ExtrapCiHigh}] &
\claim{ExtrapImproved}/\claim{ExtrapDesignCount} \\
Overall & \claim{OverallSftPenalized} & \claim{OverallGrpoPenalized} &
\claim{OverallGain} [\claim{OverallCiLow}, \claim{OverallCiHigh}] &
\claim{OverallImproved}/\claim{DesignCount} \\
\bottomrule
\end{tabular}
\end{table}
"""


def table_family(rows: list[dict], claims: Claims, primary_sources: list[str]) -> str:
    family_names = ("fir", "firr", "poly", "iir", "med")
    labels = {"fir": "FIR", "firr": "Reverse FIR", "poly": "Polynomial",
              "iir": "IIR", "med": "Median"}
    ids = {"fir": "Fir", "firr": "Firr", "poly": "Poly", "iir": "Iir", "med": "Med"}
    lines = [
        "% AUTO-GENERATED by analyze_main_results.py. DO NOT EDIT.",
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Primary endpoint by circuit family, pooling frozen regimes.}",
        r"\label{tab:family-verified}",
        r"\small",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Family & Designs & SFT & GRPO & Improved \\",
        r"\midrule",
    ]
    for fam in family_names:
        selected = [r for r in rows if r["family"] == fam]
        a = aggregate(selected)
        prefix = ids[fam]
        sources = primary_sources
        claims.add(f"Family{prefix}Count", len(selected), str(len(selected)), "designs",
                   "Count frozen held-out designs in this family.", sources)
        claims.add(f"Family{prefix}Sft", a["sft"]["penalized_fmax"], fmt(a["sft"]["penalized_fmax"]), "MHz",
                   "Mean per-design penalized equal-sample Fmax within family.", sources)
        claims.add(f"Family{prefix}Grpo", a["grpo"]["penalized_fmax"], fmt(a["grpo"]["penalized_fmax"]), "MHz",
                   "Mean per-design penalized equal-sample Fmax within family.", sources)
        claims.add(f"Family{prefix}Improved", a["improved"], str(a["improved"]), "designs",
                   "Count positive paired per-design differences within family.", sources)
        lines.append(
            f"{labels[fam]} & \\claim{{Family{prefix}Count}} & \\claim{{Family{prefix}Sft}} & "
            f"\\claim{{Family{prefix}Grpo}} & \\claim{{Family{prefix}Improved}}/\\claim{{Family{prefix}Count}} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def table_replication() -> str:
    return r"""% AUTO-GENERATED by analyze_main_results.py. DO NOT EDIT.
\begin{table}[t]
\centering
\caption{Second-backbone replication on the earlier three-family split. Values
are penalized equal-sample post-route frequency; failures score zero.}
\label{tab:qwen-replication}
\small
\begin{tabular}{lrrrr}
\toprule
Regime & Designs & SFT & GRPO & Improved \\
\midrule
Interpolation & \claim{QwenInterpDesignCount} &
\claim{QwenInterpSftPenalized} & \claim{QwenInterpGrpoPenalized} &
\claim{QwenInterpImproved}/\claim{QwenInterpDesignCount} \\
Extrapolation & \claim{QwenExtrapDesignCount} &
\claim{QwenExtrapSftPenalized} & \claim{QwenExtrapGrpoPenalized} &
\claim{QwenExtrapImproved}/\claim{QwenExtrapDesignCount} \\
Overall & \claim{QwenDesignCount} & \claim{QwenOverallSftPenalized} &
\claim{QwenOverallGrpoPenalized} &
\claim{QwenOverallImproved}/\claim{QwenDesignCount} \\
\bottomrule
\end{tabular}
\end{table}
"""


def table_context() -> str:
    return r"""% AUTO-GENERATED by analyze_main_results.py. DO NOT EDIT.
\begin{table}[t]
\centering
\caption{Same-task per-draw context on the frozen design set. The stored API
arms use fewer samples and test one prompt configuration, so they are diagnostic
baselines rather than a frontier-model ranking.}
\label{tab:context-verified}
\small
\begin{tabular}{lrrrr}
\toprule
Policy or arm & Samples/design & Penalized & Conditional & Correct [\%] \\
\midrule
API, same prompt & \claim{FrontierSamplesPerDesign} &
\claim{FrontierPlainPenalized} & \claim{FrontierPlainConditional} &
\claim{FrontierPlainCorrectness} \\
API, timing prompt & \claim{FrontierSamplesPerDesign} &
\claim{FrontierFastPenalized} & \claim{FrontierFastConditional} &
\claim{FrontierFastCorrectness} \\
SFT & \claim{SamplesPerDesign} & \claim{OverallSftPenalized} &
\claim{OverallSftConditional} & \claim{OverallSftCorrectness} \\
GRPO & \claim{SamplesPerDesign} & \claim{OverallGrpoPenalized} &
\claim{OverallGrpoConditional} & \claim{OverallGrpoCorrectness} \\
\bottomrule
\end{tabular}
\end{table}
"""


def table_ppa() -> str:
    return r"""% AUTO-GENERATED by analyze_main_results.py. DO NOT EDIT.
\begin{table}[t]
\centering
\caption{Physical-cost diagnostics on the frozen primary samples, conditional
on oracle-correct, successfully implemented samples. Power is Vivado's
vectorless estimate.}
\label{tab:ppa-verified}
\small
\begin{tabular}{lrrr}
\toprule
Metric & SFT & GRPO & GRPO/SFT \\
\midrule
LUTs & \claim{PpaSftLut} & \claim{PpaGrpoLut} & \claim{PpaLutRatio} \\
Flip-flops & \claim{PpaSftFf} & \claim{PpaGrpoFf} & \claim{PpaFfRatio} \\
DSP blocks & \claim{PpaSftDsp} & \claim{PpaGrpoDsp} & \claim{PpaDspRatio} \\
Vectorless power [W] & \claim{PpaSftPower} & \claim{PpaGrpoPower} & \claim{PpaPowerRatio} \\
\bottomrule
\end{tabular}
\end{table}
"""


def table_bestofn() -> str:
    return r"""% AUTO-GENERATED by analyze_main_results.py. DO NOT EDIT.
\begin{table}[t]
\centering
\caption{One GRPO draw versus an unattainable perfect selector over SFT draws.
All entries use the primary zero-penalized endpoint.}
\label{tab:bestof-verified}
\small
\begin{tabular}{lrrrrrr}
\toprule
Regime & SFT one & SFT eight & SFT sixteen & SFT thirty-two & SFT forty-eight & GRPO one \\
\midrule
Interpolation & \claim{InterpSftBestofOne} & \claim{InterpSftBestofEight} &
\claim{InterpSftBestofSixteen} & \claim{InterpSftBestofThirtytwo} &
\claim{InterpSftBestofFortyeight} & \claim{InterpGrpoOne} \\
Extrapolation & \claim{ExtrapSftBestofOne} & \claim{ExtrapSftBestofEight} &
\claim{ExtrapSftBestofSixteen} & \claim{ExtrapSftBestofThirtytwo} &
\claim{ExtrapSftBestofFortyeight} & \claim{ExtrapGrpoOne} \\
\bottomrule
\end{tabular}
\end{table}
"""


def table_trajectory() -> str:
    rows = []
    for name in ("Start", "Early", "Middle", "Late", "Final"):
        rows.append(
            f"\\claim{{Trajectory{name}Step}} & \\claim{{Trajectory{name}Proxy}} & "
            f"\\claim{{Trajectory{name}Penalized}} & \\claim{{Trajectory{name}Conditional}} & "
            f"\\claim{{Trajectory{name}Correctness}} \\\\"
        )
    return "\n".join([
        "% AUTO-GENERATED by analyze_main_results.py. DO NOT EDIT.",
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Bounded diagnostic on the FIR/FIRR training trajectory. Proxy reward is not an evaluation result; measured columns use Vivado.}",
        r"\label{tab:trajectory-verified}",
        r"\small",
        r"\begin{tabular}{rrrrr}",
        r"\toprule",
        r"Step & Proxy & Penalized & Conditional & Correct [\%] \\",
        r"\midrule",
        *rows,
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ])


def table_board(claims: Claims) -> tuple[str, dict]:
    """Generate a board table only from the reserved live-sweep artifact."""
    selection_path = SYMMETRIC_BOARD_DIR / "selection_manifest.json"
    result_path = SYMMETRIC_BOARD_DIR / "catalog_fmax.json"
    if not result_path.is_file():
        return (
            "% AUTO-GENERATED by analyze_main_results.py. DO NOT EDIT.\n"
            "% No table: the symmetric live-board measurement artifact is absent.\n"
            "\\emph{No symmetric live-board frequency is reported because the "
            "live sweep artifact has not yet been captured.}\n",
            {"status": "pending"},
        )
    if not selection_path.is_file():
        raise RuntimeError("board result exists without selection_manifest.json")

    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("measurement_kind") != "live_pynq_clock_sweep":
        raise RuntimeError("reserved board result is not marked as a live PYNQ sweep")
    expected_hash = sha256(selection_path)
    recorded_hash = result.get("provenance", {}).get("selection_manifest_sha256")
    if recorded_hash != expected_hash:
        raise RuntimeError("board result selection-manifest hash does not match local protocol")
    if not result.get("summary", {}).get("all_entries_have_fmax"):
        raise RuntimeError("board result is incomplete; at least one entry has no measured Fmax")

    sels = result.get("sels", {})
    measured = result.get("table", {})
    pairs = collections.OrderedDict()
    for entry, meta in sorted(sels.items(), key=lambda item: item[1].get("sel", 10**9)):
        if meta.get("role") != "dut":
            continue
        design = meta.get("design")
        policy = meta.get("policy")
        if not design or policy not in EXPECTED_POLICIES:
            raise RuntimeError(f"board selection lacks policy/design metadata: {entry}")
        if entry not in measured or measured[entry].get("silicon_fmax") is None:
            raise RuntimeError(f"board table lacks a measurement for {entry}")
        pairs.setdefault(design, {})[policy] = {
            "entry": entry,
            "fmax": float(measured[entry]["silicon_fmax"]),
            "gate": measured[entry].get("gate"),
        }
    if not pairs or any(set(pair) != set(EXPECTED_POLICIES) for pair in pairs.values()):
        raise RuntimeError("board result does not contain complete SFT/GRPO design pairs")

    sources = [file_span(selection_path), file_span(result_path)]
    claims.add("BoardPairCount", len(pairs), str(len(pairs)), "design pairs",
               "Count complete symmetric SFT/GRPO pairs in the live sweep artifact.", sources)
    words = ("First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh")
    lines = [
        "% AUTO-GENERATED by analyze_main_results.py. DO NOT EDIT.",
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Live silicon clock sweep for the historical post-hoc design set, using the same count-weighted-median rule for both policies. A leading inequality denotes a canary-limited lower bound.}",
        r"\label{tab:board-verified}",
        r"\small",
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"Design & SFT & GRPO & Ratio \\",
        r"\midrule",
    ]
    ratios = []
    for index, (design, pair) in enumerate(pairs.items()):
        if index >= len(words):
            raise RuntimeError("extend board claim word IDs for additional pairs")
        word = words[index]
        sft = pair["sft"]
        grpo = pair["grpo"]
        ratio = grpo["fmax"] / sft["fmax"]
        ratios.append(ratio)
        grpo_limited = grpo["gate"] == "TOO CLOSE TO CANARY"
        sft_limited = sft["gate"] == "TOO CLOSE TO CANARY"
        prefix_s = r"\ensuremath{\geq}" if sft_limited else ""
        prefix_g = r"\ensuremath{\geq}" if grpo_limited else ""
        prefix_r = r"\ensuremath{\geq}" if grpo_limited and not sft_limited else ""
        claims.add(f"Board{word}Sft", sft["fmax"], prefix_s + fmt(sft["fmax"]), "MHz",
                   "Median over repeated live-board clock sweeps for the symmetric SFT entry.", sources)
        claims.add(f"Board{word}Grpo", grpo["fmax"], prefix_g + fmt(grpo["fmax"]), "MHz",
                   "Median over repeated live-board clock sweeps for the symmetric GRPO entry.", sources)
        claims.add(f"Board{word}Ratio", ratio, prefix_r + fmt(ratio, 2), "ratio",
                   "GRPO silicon Fmax divided by paired SFT silicon Fmax; lower-bound marking follows canary gate.", sources)
        lines.append(
            f"\\texttt{{{design}}} & \\claim{{Board{word}Sft}} & "
            f"\\claim{{Board{word}Grpo}} & \\claim{{Board{word}Ratio}} \\\\"
        )
    claims.add("BoardMinimumRatio", min(ratios), fmt(min(ratios), 2), "ratio",
               "Minimum GRPO/SFT ratio across complete symmetric board pairs.", sources)
    claims.add("BoardMaximumRatio", max(ratios), fmt(max(ratios), 2), "ratio",
               "Maximum GRPO/SFT ratio across complete symmetric board pairs.", sources)
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines), {
        "status": "measured",
        "pairs": pairs,
        "minimum_ratio": min(ratios),
        "maximum_ratio": max(ratios),
    }


def provenance_markdown(claims: Claims) -> str:
    lines = [
        "# Generated manuscript claim ledger",
        "",
        "This file is generated by `analyze_main_results.py`; do not edit it.",
        "Every `\\claim{...}` used by the manuscript resolves through this ledger.",
        "",
        "| Claim | Display | Unit | Artifact source(s) |",
        "|---|---:|---|---|",
    ]
    for key, claim in claims.data.items():
        sources = "<br>".join(f"`{s}`" for s in claim["sources"])
        lines.append(f"| `{key}` | {claim['display']} | {claim['unit']} | {sources} |")
    lines.append("")
    return "\n".join(lines)


def write_figures(rows: list[dict], trajectory: list[dict]):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIGURES.mkdir(parents=True, exist_ok=True)
    colors = {"sft": "#7fb3d5", "grpo": "#1f4e79"}

    def save_pair(fig, stem: str):
        for ext in ("pdf", "png"):
            kwargs = {"dpi": 220, "bbox_inches": "tight"}
            if ext == "pdf":
                kwargs["metadata"] = {"CreationDate": None, "ModDate": None}
            fig.savefig(FIGURES / f"{stem}.{ext}", **kwargs)

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.45))
    for ax, regime, title in zip(axes, ("interp", "extrap"), ("Interpolation", "Extrapolation")):
        selected = [r for r in rows if r["regime"] == regime]
        x = np.arange(len(selected))
        s = [r["sft"]["penalized_fmax"] for r in selected]
        g = [r["grpo"]["penalized_fmax"] for r in selected]
        ax.plot(x, s, "o", ms=3, color=colors["sft"], label="SFT")
        ax.plot(x, g, "D", ms=3, color=colors["grpo"], label="GRPO")
        for i, (a, b) in enumerate(zip(s, g)):
            ax.plot([i, i], [a, b], color="#aaaaaa", lw=0.5, zorder=0)
        ax.axhline(0, color="black", lw=0.4)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels([r["design"] for r in selected], rotation=90, fontsize=5)
        ax.set_ylabel("Penalized equal-sample $F_{max}$ (MHz)")
    axes[0].legend(frameon=False, ncol=2)
    fig.tight_layout()
    save_pair(fig, "fig_main_verified")
    plt.close(fig)

    ordered = sorted(rows, key=lambda row: (
        ("fir", "firr", "poly", "iir", "med").index(row["family"]),
        row["design"],
    ))
    fig, ax = plt.subplots(figsize=(7.0, 2.75))
    for index, row in enumerate(ordered):
        for policy, offset, marker in (("sft", -0.17, "o"), ("grpo", 0.17, "D")):
            for candidate in row[policy]["candidates"]:
                ax.scatter(
                    index + offset,
                    candidate.fmax,
                    s=6.0 + 5.0 * candidate.count,
                    marker=marker,
                    facecolor=colors[policy],
                    edgecolor="black",
                    linewidth=0.3,
                    alpha=0.82,
                    zorder=3,
                )
    ax.set_xticks(range(len(ordered)))
    ax.set_xticklabels([row["design"] for row in ordered], rotation=90, fontsize=5.5)
    ax.set_ylabel("Real post-route $F_{max}$ (MHz)")
    handles = [
        plt.Line2D([], [], marker=marker, color="none", markerfacecolor=colors[policy],
                   markeredgecolor="black", markersize=5, label=policy.upper())
        for policy, marker in (("sft", "o"), ("grpo", "D"))
    ]
    ax.legend(handles=handles, frameon=False, ncol=2, loc="upper left")
    ax.set_title(
        "Distinct correct implementations; marker area is proportional to original sample count",
        fontsize=7.5,
    )
    fig.tight_layout()
    save_pair(fig, "fig_mechanism_verified")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(3.5, 2.35))
    steps = [r["step"] for r in trajectory]
    ax.plot(steps, [r["proxy_fmax"] for r in trajectory], "o-", label="Proxy reward")
    ax.plot(steps, [r["conditional_fmax"] for r in trajectory], "s-", label="Vivado, correct only")
    ax.plot(steps, [r["penalized_fmax"] for r in trajectory], "^-", label="Vivado, penalized")
    ax.set_xlabel("Training step")
    ax.set_ylabel("Frequency (MHz)")
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    save_pair(fig, "fig_trajectory_verified")
    plt.close(fig)


def render_outputs() -> tuple[dict[pathlib.Path, str], list[dict], list[dict], dict]:
    candidates, provenance = load_eval_dirs(PRIMARY_DIRS)
    rows = make_design_rows(candidates)
    bestof = bestof_summary(rows)
    trajectory, trajectory_sources = load_trajectory()
    primary_sources = source_spans(PRIMARY_DIRS)
    base, base_sources = load_primary_base()
    mechanism = mechanism_summary(rows)
    qwen_rows, qwen_sources = load_policy_dataset(
        QWEN_DIR, ("sft", "grpo"), expected_designs=22, expected_n=48,
        expected_families=3, expected_regimes={"interp": 14, "extrap": 8},
    )
    frontier_rows, frontier_sources = load_policy_dataset(
        FRONTIER_DIR, ("apiplain", "apifast"), expected_designs=30, expected_n=8,
        expected_families=5, expected_regimes={"interp": 19, "extrap": 11},
        summary_filename="frontier_summary.json",
    )
    if {row["design"] for row in frontier_rows} != {row["design"] for row in rows}:
        raise RuntimeError("stored API baseline does not match the frozen primary design set")
    verilogeval, verilogeval_sources = load_verilogeval()
    hls, hls_sources = load_hls_context()
    reflow, reflow_sources = load_reflow_diagnostic()
    protocol, protocol_sources = load_protocol_config()
    claims, result = build_claims(
        rows, bestof, trajectory, primary_sources, trajectory_sources
    )
    add_secondary_claims(
        claims, result, primary_sources, base, base_sources, mechanism,
        qwen_rows, qwen_sources, frontier_rows, frontier_sources,
        verilogeval, verilogeval_sources, hls, hls_sources,
        reflow, reflow_sources, protocol, protocol_sources,
    )
    family_tex = table_family(rows, claims, primary_sources)
    board_tex, board_summary = table_board(claims)
    result["provenance"] = provenance
    result["bootstrap"] = {"seed": BOOTSTRAP_SEED, "replicates": BOOTSTRAP_REPS}
    board_selection = SYMMETRIC_BOARD_DIR / "selection_manifest.json"
    board_bit = SYMMETRIC_BOARD_DIR / "out" / "system_holdout_symmetric.bit"
    board_hwh = SYMMETRIC_BOARD_DIR / "out" / "system_holdout_symmetric.hwh"
    board_result = SYMMETRIC_BOARD_DIR / "catalog_fmax.json"
    if board_result.is_file():
        board_status = "measured"
    elif board_bit.is_file() and board_hwh.is_file():
        board_status = "bitstream_built_board_sweep_pending"
    elif board_selection.is_file():
        board_status = "symmetric_selection_prepared"
    else:
        board_status = "pending"
    result["symmetric_board"] = {
        "status": board_status,
        "selection_manifest": rel(board_selection),
        "selection_manifest_sha256": sha256(board_selection) if board_selection.is_file() else None,
        "bitstream": rel(board_bit),
        "bitstream_sha256": sha256(board_bit) if board_bit.is_file() else None,
        "hwh": rel(board_hwh),
        "hwh_sha256": sha256(board_hwh) if board_hwh.is_file() else None,
        "required_measurement_artifact": rel(board_result),
        "measurement_summary": board_summary,
    }
    claims_json = {
        "schema": 1,
        "generator": "analyze_main_results.py",
        "claims": claims.data,
    }
    outputs = {
        GENERATED / "claims.tex": tex_claims(claims),
        GENERATED / "claims.json": json.dumps(claims_json, indent=2) + "\n",
        GENERATED / "claim_provenance.md": provenance_markdown(claims),
        GENERATED / "main_results.json": json.dumps(result, indent=2) + "\n",
        GENERATED / "table_main.tex": table_main(),
        GENERATED / "table_family.tex": family_tex,
        GENERATED / "table_replication.tex": table_replication(),
        GENERATED / "table_context.tex": table_context(),
        GENERATED / "table_ppa.tex": table_ppa(),
        GENERATED / "table_bestofn.tex": table_bestofn(),
        GENERATED / "table_trajectory.tex": table_trajectory(),
        GENERATED / "table_board.tex": board_tex,
    }
    return outputs, rows, trajectory, result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated text outputs are stale")
    parser.add_argument("--no-figures", action="store_true", help="skip deterministic plot regeneration")
    args = parser.parse_args()

    outputs, rows, trajectory, result = render_outputs()
    if args.check:
        stale = []
        for path, expected in outputs.items():
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                stale.append(rel(path))
        if stale:
            print("STALE generated paper artifacts:", file=sys.stderr)
            for path in stale:
                print(f"  {path}", file=sys.stderr)
            print("run: python analyze_main_results.py", file=sys.stderr)
            return 1
        print(f"OK: {len(rows)} designs; all generated text artifacts are current")
        return 0

    GENERATED.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"wrote {rel(path)}")
    if not args.no_figures:
        write_figures(rows, trajectory)
        print("wrote paper/figures/fig_main_verified.{pdf,png}")
        print("wrote paper/figures/fig_mechanism_verified.{pdf,png}")
        print("wrote paper/figures/fig_trajectory_verified.{pdf,png}")

    for regime in ("interp", "extrap", "overall"):
        a = result["aggregates"][regime]
        lo, hi = result["bootstrap_ci"][regime]
        print(
            f"{regime:7s}: SFT {a['sft']['penalized_fmax']:.1f} -> "
            f"GRPO {a['grpo']['penalized_fmax']:.1f} MHz; gain {a['gain_mhz']:+.1f} "
            f"[{lo:.1f}, {hi:.1f}], improved {a['improved']}/{a['designs']}"
        )
    print(f"symmetric board artifact: {result['symmetric_board']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
