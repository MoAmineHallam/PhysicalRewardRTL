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
  paper/generated/table_board.tex
  paper/figures/fig_main_verified.{pdf,png}
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
            sources = sorted({c.manifest_source for c in cs} | {c.ppa_source for c in cs})
            policy_rows[policy] = {
                "n": n,
                "correct": correct,
                "compiled": sum(c.count for c in cs if c.compiled),
                "penalized_fmax": measured_sum / n,
                "conditional_fmax": measured_sum / correct if correct else 0.0,
                "correct_pct": 100.0 * correct / n,
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
        "bestof": bestof,
        "trajectory": trajectory,
    }
    return claims, result


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
    for ext in ("pdf", "png"):
        fig.savefig(FIGURES / f"fig_main_verified.{ext}", dpi=220, bbox_inches="tight")
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
    for ext in ("pdf", "png"):
        fig.savefig(FIGURES / f"fig_trajectory_verified.{ext}", dpi=220, bbox_inches="tight")
    plt.close(fig)


def render_outputs() -> tuple[dict[pathlib.Path, str], list[dict], list[dict], dict]:
    candidates, provenance = load_eval_dirs(PRIMARY_DIRS)
    rows = make_design_rows(candidates)
    bestof = bestof_summary(rows)
    trajectory, trajectory_sources = load_trajectory()
    primary_sources = source_spans(PRIMARY_DIRS)
    claims, result = build_claims(
        rows, bestof, trajectory, primary_sources, trajectory_sources
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
