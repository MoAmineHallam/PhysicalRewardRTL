#!/usr/bin/env python3
"""Generate the complete pre-writing figure package from frozen artifacts.

The plotting code contains no measured headline values.  It reads the sealed
Study 2 result, bounded secondary analysis, descriptive board result, and the
already-generated historical result ledger.  Every figure is emitted as PDF
and PNG, and ``paper/generated/figure_manifest.json`` records the exact arrays,
input hashes, source line spans, and output hashes.

Run from the repository root:

    python paper/make_verified_figures.py
    python paper/make_verified_figures.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import shutil
import sys
import tempfile
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np
from diagram_art import training_diagram, board_diagram


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIGURES = ROOT / "paper" / "figures"
GENERATED = ROOT / "paper" / "generated"
SCRIPT = pathlib.Path(__file__).resolve()

PRIMARY_PATH = ROOT / "sealed_results_study2.json"
SPLIT_PATH = ROOT / "sealed_split.json"
SECONDARY_PATH = ROOT / "study2_secondary_results.json"
BOARD_PATH = ROOT / "study2_board_results.json"
BOARD_SPEC_PATH = ROOT / "study2_board_spec.json"
BOARD_AMENDMENT_PATH = ROOT / "study2_board_protocol_amendment.json"
HISTORICAL_PATH = GENERATED / "main_results.json"
FIG1_SOURCE = ROOT / "paper" / "sections" / "03_method.tex"

MANIFEST_PATH = GENERATED / "figure_manifest.json"
PROVENANCE_PATH = GENERATED / "figure_provenance.md"
CAPTIONS_PATH = GENERATED / "figure_captions.md"

INPUT_PATHS = (
    ROOT / "paper" / "diagram_art.py",
    ROOT / "rtl" / "sealed_study2_board" / "dut_top.v",
    ROOT / "rtl" / "la_axi_fast.v",
    ROOT / "gen_study2_board.py",
    ROOT / "sweep_catalog.py",
    PRIMARY_PATH,
    SPLIT_PATH,
    SECONDARY_PATH,
    BOARD_PATH,
    BOARD_SPEC_PATH,
    BOARD_AMENDMENT_PATH,
    HISTORICAL_PATH,
    FIG1_SOURCE,
)

COLORS = {
    "sft": "#8DA0AE",
    "rf": "#0072B2",
    "mlp": "#E69F00",
    "correctness": "#009E73",
    "negative": "#D55E00",
    "neutral": "#6B7280",
    "light": "#E5E7EB",
    "interp": "#0072B2",
    "extrap": "#E69F00",
}

FAMILY_LABELS = {
    "fir": "FIR",
    "firr": "Reverse FIR",
    "poly": "Polynomial",
    "iir": "IIR",
    "med": "Median",
}

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8,
        "svg.hashsalt": "fpga-tcad-figures",
        "axes.labelsize": 8,
        "axes.titlesize": 8.5,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.20,
        "grid.linewidth": 0.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)


class FigureInputError(RuntimeError):
    pass


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256(path: pathlib.Path) -> str:
    raw = path.read_bytes()
    # Git normalizes these text artifacts; Windows checkouts may restore CRLF.
    # Binary PDF/PNG exports always retain byte-exact hashes.
    if path.suffix.lower() in {".py", ".v", ".json", ".tex", ".svg"}:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def span(path: pathlib.Path) -> str:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        n_lines = sum(1 for _ in handle)
    return f"{rel(path)}:1-{n_lines}"


def read_json(path: pathlib.Path) -> dict:
    if not path.is_file():
        raise FigureInputError(f"missing required artifact: {rel(path)}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def close(a: float, b: float, tolerance: float = 1e-9) -> bool:
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tolerance)


def assert_close(a: float, b: float, label: str) -> None:
    if not close(a, b):
        raise FigureInputError(f"cross-artifact mismatch for {label}: {a} != {b}")


def collect_data() -> tuple[dict, dict[str, str]]:
    primary = read_json(PRIMARY_PATH)
    split = read_json(SPLIT_PATH)
    secondary = read_json(SECONDARY_PATH)
    board = read_json(BOARD_PATH)
    board_spec = read_json(BOARD_SPEC_PATH)
    amendment = read_json(BOARD_AMENDMENT_PATH)
    historical = read_json(HISTORICAL_PATH)

    if primary.get("outcome") != "full_two_regime_repair":
        raise FigureInputError("sealed Study 2 primary outcome is not the frozen repair outcome")
    if secondary.get("primary_outcome_unchanged") != primary["outcome"]:
        raise FigureInputError("secondary analysis changed the primary outcome")
    if board.get("primary_outcome_unchanged") != primary["outcome"]:
        raise FigureInputError("board analysis changed the primary outcome")
    if not board.get("protocol_amended"):
        raise FigureInputError("board result lost its required amendment disclosure")
    if len(primary.get("designs", [])) != 20 or split.get("n_designs") != 20:
        raise FigureInputError("expected exactly 20 sealed Study 2 designs")

    meta = {
        row["design"]: {"family": row["family"], "regime": row["regime"]}
        for row in split["designs"]
    }
    if set(meta) != set(primary["designs"]):
        raise FigureInputError("sealed split and primary result design identities differ")

    rf_all = primary["report"]["rf"]["combined"]["all"]
    direct_all = secondary["direct_rf_mlp"]["all"]
    assert_close(rf_all["arm_equal"], direct_all["rf_equal"], "overall RF Fmax")
    assert_close(rf_all["sft_equal"], direct_all["sft_equal"], "overall SFT Fmax")

    regime_rank = {"interp": 0, "extrap": 1}
    design_order = sorted(
        primary["designs"],
        key=lambda d: (regime_rank[meta[d]["regime"]], primary["designs"].index(d)),
    )
    design_rows = []
    for design in design_order:
        sft = float(primary["sft"][design]["equal"])
        rf = float(primary["arms"]["rf"][design]["equal"])
        design_rows.append(
            {
                "design": design,
                "family": meta[design]["family"],
                "regime": meta[design]["regime"],
                "sft": sft,
                "rf": rf,
                "difference": rf - sft,
            }
        )

    primary_forest = []
    for scope, label in (("all", "Overall"), ("interp", "Interpolation"), ("extrap", "Extrapolation")):
        row = primary["report"]["rf"]["combined"][scope]
        primary_forest.append(
            {
                "label": label,
                "mean": float(row["mean_diff"]),
                "ci_lo": float(row["ci_lo"]),
                "ci_hi": float(row["ci_hi"]),
                "has_ci": True,
            }
        )
    for index, row in enumerate(primary["report"]["rf"]["per_seed"], 1):
        primary_forest.append(
            {
                "label": f"RF seed {index}",
                "mean": float(row["all"]),
                "ci_lo": None,
                "ci_hi": None,
                "has_ci": False,
            }
        )

    reports = primary["report"]
    controls = {
        "points": [
            {
                "arm": "SFT",
                "key": "sft",
                "correctness_pct": 100.0 * float(reports["rf"]["combined"]["all"]["sft_correct"]),
                "fmax_mhz": float(reports["rf"]["combined"]["all"]["sft_equal"]),
            },
            {
                "arm": "Correctness only",
                "key": "correctness",
                "correctness_pct": 100.0 * float(reports["correctness"]["combined"]["all"]["arm_correct"]),
                "fmax_mhz": float(reports["correctness"]["combined"]["all"]["arm_equal"]),
            },
            {
                "arm": "Original MLP",
                "key": "mlp",
                "correctness_pct": 100.0 * float(reports["mlp"]["combined"]["all"]["arm_correct"]),
                "fmax_mhz": float(reports["mlp"]["combined"]["all"]["arm_equal"]),
            },
            {
                "arm": "Repaired RF",
                "key": "rf",
                "correctness_pct": 100.0 * float(reports["rf"]["combined"]["all"]["arm_correct"]),
                "fmax_mhz": float(reports["rf"]["combined"]["all"]["arm_equal"]),
            },
        ],
        "contrasts": [],
    }
    for label, arm_key in (
        ("Correctness only - SFT", "correctness"),
        ("Original MLP - SFT", "mlp"),
        ("Repaired RF - SFT", "rf"),
    ):
        row = reports[arm_key]["combined"]["all"]
        controls["contrasts"].append(
            {
                "label": label,
                "mean": float(row["mean_diff"]),
                "ci_lo": float(row["ci_lo"]),
                "ci_hi": float(row["ci_hi"]),
                "key": arm_key,
            }
        )
    controls["contrasts"].append(
        {
            "label": "Repaired RF - original MLP",
            "mean": float(direct_all["rf_minus_mlp"]),
            "ci_lo": float(direct_all["ci_lo"]),
            "ci_hi": float(direct_all["ci_hi"]),
            "key": "rf",
        }
    )

    board_pairs = []
    for family, row in board["pairs"].items():
        board_pairs.append(
            {
                "family": family,
                "design": row["design"],
                "regime": row["regime"],
                "sft": float(row["sft_fmax_mhz"]),
                "rf": float(row["rf_fmax_mhz"]),
                "difference": float(row["rf_minus_sft_mhz"]),
            }
        )

    mech = historical["mechanism"]
    mechanism_rows = []
    for family in ("fir", "firr", "poly", "iir", "med"):
        row = mech["families"][family]
        mechanism_rows.append(
            {
                "family": family,
                "label": FAMILY_LABELS[family],
                "sft_dominant_mass_pct": float(row["sft"]["dominant_mass_pct"]),
                "grpo_dominant_mass_pct": float(row["grpo"]["dominant_mass_pct"]),
                "sft_effective_support": float(row["sft"]["effective_correct_implementations"]),
                "grpo_effective_support": float(row["grpo"]["effective_correct_implementations"]),
            }
        )
    overall_mech = mech["overall"]

    trajectory = [
        {
            "step": int(row["step"]),
            "proxy_fmax": float(row["proxy_fmax"]),
            "conditional_fmax": float(row["conditional_fmax"]),
            "penalized_fmax": float(row["penalized_fmax"]),
            "correct_pct": float(row["correct_pct"]),
        }
        for row in historical["trajectory"]
    ]
    repaired = []
    for regime, label in (("interp", "Interpolation"), ("extrap", "Extrapolation")):
        row = primary["late_divergence"]["by_regime"][regime]
        repaired.append(
            {
                "regime": regime,
                "label": label,
                "mid_fmax": float(row["mid_equal_fmax"]),
                "end_fmax": float(row["end_equal_fmax"]),
                "mid_reward": float(row["mid_reward"]),
                "end_reward": float(row["end_reward"]),
            }
        )

    data = {
        "figure2": {
            "designs": design_rows,
            "forest": primary_forest,
            "sft_mean_mhz": float(rf_all["sft_equal"]),
            "rf_mean_mhz": float(rf_all["arm_equal"]),
        },
        "figure3": controls,
        "figure4": {
            "pairs": board_pairs,
            "aggregate": board["descriptive_aggregate"],
            "canary": board["canary"],
            "measurement": board["measurement"],
            "selection_count": int(board_spec["design_selection"]["count"]),
            "protocol_amended": bool(board["protocol_amended"]),
            "amendment_status": amendment["amendment"]["scientific_status"],
        },
        "figure5": {
            "families": mechanism_rows,
            "overall": {
                "sft_dominant_mass_pct": float(overall_mech["sft"]["dominant_mass_pct"]),
                "grpo_dominant_mass_pct": float(overall_mech["grpo"]["dominant_mass_pct"]),
                "sft_effective_support": float(overall_mech["sft"]["effective_correct_implementations"]),
                "grpo_effective_support": float(overall_mech["grpo"]["effective_correct_implementations"]),
            },
            "sft_support_at_or_above_grpo_conditional": int(mech["sft_support_at_or_above_grpo_conditional"]),
            "n_designs": int(historical["aggregates"]["overall"]["designs"]),
        },
        "figure6": {"historical": trajectory, "repaired": repaired},
    }

    source_spans = {rel(path): span(path) for path in INPUT_PATHS if path.suffix != ".png"}
    return data, source_spans


def save_pair(fig: plt.Figure, outdir: pathlib.Path, stem: str) -> list[pathlib.Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    pdf = outdir / f"{stem}.pdf"
    png = outdir / f"{stem}.png"
    fig.savefig(
        pdf,
        metadata={
            "Creator": "paper/make_verified_figures.py",
            "Producer": "Matplotlib",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    fig.savefig(png, dpi=300, metadata={"Software": "paper/make_verified_figures.py"})
    plt.close(fig)
    return [pdf, png]


def figure1(outdir: pathlib.Path) -> list[pathlib.Path]:
    return training_diagram(outdir)


def figure2(data: dict, outdir: pathlib.Path) -> list[pathlib.Path]:
    fig = plt.figure(figsize=(7.16, 4.55))
    ax = fig.add_axes([.20,.15,.35,.74])
    forest = fig.add_axes([.76,.20,.22,.65])
    fig.text(.02,.96,"(a) Per-design physical endpoint", fontsize=9, fontweight="bold")
    fig.text(.64,.96,"(b) Paired RF − SFT effects", fontsize=9, fontweight="bold")
    rows = data["designs"]
    y = np.arange(len(rows))
    for yi, row in zip(y, rows):
        color = COLORS["rf"] if row["difference"] > 0 else (
            COLORS["negative"] if row["difference"] < 0 else COLORS["neutral"])
        ax.plot([row["sft"],row["rf"]],[yi,yi],color=color,lw=1)
    for key,marker,label in (("sft","o","SFT"),("rf","D","RF")):
        ax.scatter([r[key] for r in rows],y,s=21,marker=marker,
                   c=COLORS[key],edgecolor="black",lw=.35,label=label,zorder=3)
    ax.set_yticks(y,[("I  " if r["regime"]=="interp" else "E  ")+r["design"] for r in rows],fontsize=8.5)
    ax.set_ylim(len(rows)-.4,-.6)
    split=sum(r["regime"]=="interp" for r in rows)
    ax.axhline(split-.5,color="#858585",lw=.65,ls="--")
    ax.set_xlabel("Failure-penalized frequency (MHz)",fontsize=8.6)
    ax.tick_params(axis="x",labelsize=8.5)
    ax.legend(frameon=False,ncol=2,loc="upper center",bbox_to_anchor=(.5,1.08),fontsize=8.5)
    frows=data["forest"]
    labels=("Overall","Interpolation","Extrapolation","RF seed one","RF seed two")
    for yi,row in enumerate(frows):
        if row["has_ci"]:
            forest.errorbar(row["mean"],yi,
                xerr=[[row["mean"]-row["ci_lo"]],[row["ci_hi"]-row["mean"]]],
                fmt="D",ms=4.5,capsize=3,lw=1.1,color=COLORS["rf"])
        else:
            forest.plot(row["mean"],yi,"o",ms=4.5,color=COLORS["neutral"])
    forest.axvline(0,color="#505050",lw=.8)
    forest.set_yticks(range(len(frows)),labels,fontsize=8.5)
    forest.set_ylim(len(frows)-.4,-.6)
    forest.set_xlim(-8,115)
    forest.set_xlabel("Difference (MHz)",fontsize=9)
    forest.tick_params(axis="x",labelsize=8.5)
    fig.text(.02,.02,"I: interpolation   E: extrapolation",fontsize=8.5)
    fig.text(.64,.07,"Intervals: paired design bootstrap\nSeed points: no added intervals",fontsize=8.3)
    return save_pair(fig,outdir,"fig02_study2_primary")


def figure3(data: dict, outdir: pathlib.Path) -> list[pathlib.Path]:
    fig=plt.figure(figsize=(7.16,2.75))
    ax=fig.add_axes([.11,.22,.37,.65])
    forest=fig.add_axes([.73,.22,.25,.65])
    fig.text(.11,.95,"(a) Correctness and physical utility",fontsize=9,fontweight="bold")
    fig.text(.65,.95,"(b) Paired policy contrasts",fontsize=9,fontweight="bold")
    offsets={"sft":(5,5),"rf":(5,4),"mlp":(5,5),"correctness":(-7,6)}
    names={"sft":"SFT","rf":"RF","mlp":"MLP","correctness":"Correctness only"}
    for row in data["points"]:
        key=row["key"]
        ax.scatter(row["correctness_pct"],row["fmax_mhz"],s=35,c=COLORS[key],
                   edgecolor="black",lw=.5,zorder=3)
        ax.annotate(names[key],(row["correctness_pct"],row["fmax_mhz"]),
                    xytext=offsets[key],textcoords="offset points",fontsize=8.5,
                    ha="right" if key=="correctness" else "left")
    ax.set(xlim=(47,71),ylim=(15,110))
    ax.set_xlabel("Oracle-passing draws (%)",fontsize=9)
    ax.set_ylabel("Penalized frequency (MHz)",fontsize=9)
    ax.tick_params(labelsize=8.5)
    rows=data["contrasts"]
    labels=("Correctness\n− SFT","MLP − SFT","RF − SFT","RF − MLP")
    forest.axvline(0,color="#505050",lw=.8)
    for yi,row in enumerate(rows):
        forest.errorbar(row["mean"],yi,
            xerr=[[row["mean"]-row["ci_lo"]],[row["ci_hi"]-row["mean"]]],
            fmt="D",ms=4.5,capsize=3,lw=1.1,color=COLORS[row["key"]])
    forest.set_yticks(range(len(rows)),labels,fontsize=8.5)
    forest.set_ylim(len(rows)-.5,-.5)
    forest.set_xlim(-20,85)
    forest.set_xlabel("Difference (MHz)",fontsize=9)
    forest.tick_params(axis="x",labelsize=8.5)
    return save_pair(fig,outdir,"fig03_study2_controls")


def protocol_box(ax: plt.Axes, center_y: float, text: str, color: str) -> None:
    width, height = 0.80, 0.125
    patch = FancyBboxPatch(
        (0.10, center_y - height / 2), width, height,
        boxstyle="round,pad=0.012,rounding_size=0.012",
        facecolor=color, edgecolor="#4B5563", linewidth=0.8,
    )
    ax.add_patch(patch)
    ax.text(0.50, center_y, text, ha="center", va="center", fontsize=6.8)


def figure4(data: dict, outdir: pathlib.Path) -> list[pathlib.Path]:
    outputs = board_diagram(data, outdir)
    # A separate one-column result plot keeps the architecture legible.
    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    fig.subplots_adjust(left=.23, right=.97, bottom=.23, top=.89)
    rows = sorted(data["pairs"], key=lambda row: row["difference"], reverse=True)
    y = np.arange(len(rows))
    for yi, row in zip(y, rows):
        color = COLORS["rf"] if row["difference"] > 0 else (
            COLORS["negative"] if row["difference"] < 0 else COLORS["neutral"])
        ax.plot([row["sft"], row["rf"]], [yi-.04, yi+.04], color=color, lw=1.1)
        ax.annotate(f"{row['difference']:+.1f}", (max(row["sft"], row["rf"]), yi),
                    xytext=(4, 0), textcoords="offset points", va="center", fontsize=8)
    ax.scatter([r["sft"] for r in rows], y-.04, s=25, color=COLORS["sft"],
               edgecolor="black", linewidth=.45, marker="o", label="SFT", zorder=3)
    ax.scatter([r["rf"] for r in rows], y+.04, s=28, color=COLORS["rf"],
               edgecolor="black", linewidth=.45, marker="D", label="RF", zorder=3)
    canary = float(data["canary"]["median_fmax_mhz"])
    ax.axvline(canary, color=COLORS["neutral"], ls="--", lw=.8)
    ax.text(canary, -.72, f"Canary {canary:g} MHz", ha="right", fontsize=8)
    labels = {"fir": "FIR", "firr": "Reverse FIR", "poly": "Poly.", "iir": "IIR", "med": "Median"}
    ax.set_yticks(y, [labels[r["family"]] for r in rows], fontsize=8.5)
    ax.set_ylim(len(rows)-.5, -.5)
    ax.set_xlim(0, canary * 1.15)
    ax.set_xlabel("Measured clock boundary (MHz)", fontsize=9)
    ax.tick_params(labelsize=8.5)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(.5,-.22), ncol=2, fontsize=8.5)
    outputs += save_pair(fig, outdir, "fig04b_board_outcomes")
    return outputs


def figure5(data: dict, outdir: pathlib.Path) -> list[pathlib.Path]:
    fig, (mass, support) = plt.subplots(1, 2, figsize=(7.16, 2.75), gridspec_kw={"wspace": 0.36})
    rows = [
        {
            "label": "Overall",
            "sft_dominant_mass_pct": data["overall"]["sft_dominant_mass_pct"],
            "grpo_dominant_mass_pct": data["overall"]["grpo_dominant_mass_pct"],
            "sft_effective_support": data["overall"]["sft_effective_support"],
            "grpo_effective_support": data["overall"]["grpo_effective_support"],
        },
        *data["families"],
    ]
    y = np.arange(len(rows))
    for ax, sft_key, grpo_key, xlabel, title in (
        (mass, "sft_dominant_mass_pct", "grpo_dominant_mass_pct", "Dominant correct-candidate mass (%)", "(a) Probability concentration"),
        (support, "sft_effective_support", "grpo_effective_support", "Effective correct implementations", "(b) Effective support"),
    ):
        ax.axhspan(len(rows) - 1 - 0.42, len(rows) - 1 + 0.42, color="#FFF3D6", alpha=0.55, zorder=0)
        for yi, row in zip(y, rows):
            ax.plot([row[sft_key], row[grpo_key]], [yi, yi], color="#9CA3AF", lw=1.1)
        ax.scatter([r[sft_key] for r in rows], y, s=28, marker="o", color=COLORS["sft"],
                   edgecolor="black", linewidth=0.35, label="SFT", zorder=3)
        ax.scatter([r[grpo_key] for r in rows], y, s=31, marker="D", color=COLORS["rf"],
                   edgecolor="black", linewidth=0.35, label="Earlier GRPO", zorder=3)
        ax.set_yticks(y)
        ax.set_yticklabels([r["label"] for r in rows])
        ax.invert_yaxis()
        ax.set_xlabel(xlabel)
        ax.set_title(title, loc="left")
    mass.set_xlim(0, 100)
    support.set_xlim(left=0)
    mass.legend(frameon=False, ncol=2, loc="lower right")
    support.text(
        0.0, -0.20,
        f"SFT support already contained a candidate at least as fast as the GRPO conditional mean on "
        f"{data['sft_support_at_or_above_grpo_conditional']}/{data['n_designs']} designs.",
        transform=support.transAxes, fontsize=6.2,
    )
    fig.suptitle("Earlier 30-design mechanism: probability reallocation",
                 fontsize=8.5, y=1.01)
    return save_pair(fig, outdir, "fig05_probability_reallocation")


def figure6(data: dict, outdir: pathlib.Path) -> list[pathlib.Path]:
    fig=plt.figure(figsize=(7.16,2.9))
    old=fig.add_axes([.10,.24,.36,.62])
    repaired=fig.add_axes([.63,.24,.35,.62])
    fig.text(.10,.95,"(a) Historical proxy failure",fontsize=9,fontweight="bold")
    fig.text(.63,.95,"(b) Repaired-RF trajectory",fontsize=9,fontweight="bold")
    rows=data["historical"]
    steps=[r["step"] for r in rows]
    for key,label,color,style in (
        ("proxy_fmax","Proxy",COLORS["mlp"],"o-"),
        ("conditional_fmax","Correct only",COLORS["neutral"],"s--"),
        ("penalized_fmax","Failures = zero",COLORS["rf"],"D-")):
        old.plot(steps,[r[key] for r in rows],style,ms=3.5,lw=1.15,color=color,label=label)
    old.set_xlabel("Saved checkpoint",fontsize=9)
    old.set_ylabel("Frequency (MHz)",fontsize=9)
    old.tick_params(labelsize=8.5)
    old.legend(frameon=False,fontsize=8,loc="upper left")
    for row in data["repaired"]:
        repaired.plot([0,1],[row["mid_fmax"],row["end_fmax"]],"o-",ms=4.5,lw=1.3,
                      color=COLORS[row["regime"]],label=row["label"])
    repaired.set_xticks([0,1],["Midpoint","Endpoint"],fontsize=9)
    repaired.set(xlim=(-.18,1.18),ylim=(0,140))
    repaired.set_ylabel("Penalized frequency (MHz)",fontsize=9)
    repaired.tick_params(axis="y",labelsize=8.5)
    repaired.legend(frameon=False,fontsize=8.5,loc="center")
    return save_pair(fig,outdir,"fig06_reward_reliability")


def generate_figures(data: dict, outdir: pathlib.Path) -> list[pathlib.Path]:
    outputs = []
    outputs.extend(figure1(outdir))
    outputs.extend(figure2(data["figure2"], outdir))
    outputs.extend(figure3(data["figure3"], outdir))
    outputs.extend(figure4(data["figure4"], outdir))
    outputs.extend(figure5(data["figure5"], outdir))
    outputs.extend(figure6(data["figure6"], outdir))
    return outputs


def captions(data: dict, spans: dict[str, str]) -> str:
    f2 = data["figure2"]
    overall = f2["forest"][0]
    seeds = f2["forest"][3:]
    points = {row["key"]: row for row in data["figure3"]["points"]}
    contrasts = {row["label"]: row for row in data["figure3"]["contrasts"]}
    board = data["figure4"]
    mechanism = data["figure5"]
    repaired = {row["regime"]: row for row in data["figure6"]["repaired"]}
    trajectory = data["figure6"]["historical"]
    return f"""# Factual figure-caption skeletons

Status: pre-writing evidence text generated by `paper/make_verified_figures.py`.
These are factual caption skeletons, not manuscript prose.  Every number below
is generated from the cited artifact span.

## Figure 1 — Training and evidence boundary

Correctness-gated proxy rewards update the policy, whereas every reported
hardware result is produced after the frozen evidence boundary by the identical
physical evaluation and provenance path.

Source: `{spans[rel(FIG1_SOURCE)]}`. Native vector schematic drawn by this generator.

## Figure 2 — Sealed Study 2 primary efficacy

Panel (a) retains all {len(f2['designs'])} sealed designs and scores incorrect or
implementation-failed draws as zero.  Mean penalized equal-sample post-route
Fmax rises from {f2['sft_mean_mhz']:.1f} to {f2['rf_mean_mhz']:.1f} MHz.  Panel
(b) gives the paired RF-minus-SFT gain of {overall['mean']:+.1f} MHz with frozen
95% interval [{overall['ci_lo']:+.1f}, {overall['ci_hi']:+.1f}] MHz; the two RF
training-seed gains are {seeds[0]['mean']:+.1f} and {seeds[1]['mean']:+.1f} MHz.

Source: `{spans[rel(PRIMARY_PATH)]}`; design strata from `{spans[rel(SPLIT_PATH)]}`.

## Figure 3 — Matched controls

Correctness-only training reaches {points['correctness']['correctness_pct']:.1f}%
correctness but only {points['correctness']['fmax_mhz']:.1f} MHz penalized Fmax,
whereas repaired RF reaches {points['rf']['correctness_pct']:.1f}% correctness
and {points['rf']['fmax_mhz']:.1f} MHz.  The direct repaired-RF minus original-MLP
contrast is {contrasts['Repaired RF - original MLP']['mean']:+.1f} MHz with 95%
interval [{contrasts['Repaired RF - original MLP']['ci_lo']:+.1f},
{contrasts['Repaired RF - original MLP']['ci_hi']:+.1f}] MHz.

Sources: `{spans[rel(PRIMARY_PATH)]}`; `{spans[rel(SECONDARY_PATH)]}`.

## Figure 4 — Descriptive PYNQ-Z2 evidence

The post-primary amended protocol measures {board['selection_count']} symmetric
SFT/RF pairs in one provenance-bound image over {board['measurement']['runs']}
complete sweeps with a co-resident {board['canary']['median_fmax_mhz']:.0f}-MHz
echo canary.  All pairs are shown: {board['aggregate']['rf_wins']} RF wins,
{board['aggregate']['ties']} ties, and {board['aggregate']['rf_losses']} loss;
the descriptive mean paired difference is
{board['aggregate']['mean_paired_difference_mhz']:+.1f} MHz.  This amended subset
is descriptive, not independently confirmatory.

Sources: `{spans[rel(BOARD_PATH)]}`; `{spans[rel(BOARD_SPEC_PATH)]}`;
`{spans[rel(BOARD_AMENDMENT_PATH)]}`.

## Figure 5 — Probability reallocation

In the earlier {mechanism['n_designs']}-design study, overall dominant correct-
candidate mass changes from {mechanism['overall']['sft_dominant_mass_pct']:.1f}%
to {mechanism['overall']['grpo_dominant_mass_pct']:.1f}%, while effective correct
support changes from {mechanism['overall']['sft_effective_support']:.2f} to
{mechanism['overall']['grpo_effective_support']:.2f} implementations.  The median
family is retained as a counterexample.  SFT support already contains a candidate
at least as fast as the GRPO conditional mean on
{mechanism['sft_support_at_or_above_grpo_conditional']}/{mechanism['n_designs']}
designs.

Source: `{spans[rel(HISTORICAL_PATH)]}`.

## Figure 6 — Bounded reward-reliability subplot

In the historical trajectory, the proxy rises from
{trajectory[-2]['proxy_fmax']:.1f} to {trajectory[-1]['proxy_fmax']:.1f} MHz over
the last saved interval while penalized physical utility falls from
{trajectory[-2]['penalized_fmax']:.1f} to
{trajectory[-1]['penalized_fmax']:.1f} MHz.  Under the repaired RF reward,
interpolation is {repaired['interp']['mid_fmax']:.1f} to
{repaired['interp']['end_fmax']:.1f} MHz and extrapolation is
{repaired['extrap']['mid_fmax']:.1f} to
{repaired['extrap']['end_fmax']:.1f} MHz from midpoint to endpoint.  This is a
bounded diagnostic, not a randomized causal test of canonicalization.

Sources: `{spans[rel(HISTORICAL_PATH)]}`; `{spans[rel(PRIMARY_PATH)]}`.
"""


def provenance(data: dict, spans: dict[str, str], output_hashes: dict[str, str]) -> str:
    figure_sources = {
        "Figure 1": [rel(FIG1_SOURCE)],
        "Figure 2": [rel(PRIMARY_PATH), rel(SPLIT_PATH)],
        "Figure 3": [rel(PRIMARY_PATH), rel(SECONDARY_PATH)],
        "Figure 4": [rel(BOARD_PATH), rel(BOARD_SPEC_PATH), rel(BOARD_AMENDMENT_PATH),
                     "rtl/sealed_study2_board/dut_top.v", "rtl/la_axi_fast.v",
                     "gen_study2_board.py", "sweep_catalog.py"],
        "Board outcomes": [rel(BOARD_PATH)],
        "Figure 5": [rel(HISTORICAL_PATH)],
        "Figure 6": [rel(HISTORICAL_PATH), rel(PRIMARY_PATH)],
    }
    lines = [
        "# Verified figure provenance",
        "",
        "Generated by `paper/make_verified_figures.py`; do not hand edit.",
        "",
        "| Figure | Artifact source spans | Outputs |",
        "|---|---|---|",
    ]
    stems = {
        "Figure 1": "fig01_training_evidence_boundary_v3",
        "Figure 2": "fig02_study2_primary",
        "Figure 3": "fig03_study2_controls",
        "Figure 4": "fig04_board_architecture_v2",
        "Board outcomes": "fig04b_board_outcomes",
        "Figure 5": "fig05_probability_reallocation",
        "Figure 6": "fig06_reward_reliability",
    }
    for figure, sources in figure_sources.items():
        src = "<br>".join(f"`{spans[source]}`" for source in sources)
        matching = sorted(path for path in output_hashes if pathlib.Path(path).stem == stems[figure])
        outs = "<br>".join(f"`{path}` `{output_hashes[path][:12]}...`" for path in matching)
        lines.append(f"| {figure} | {src} | {outs} |")
    lines.extend(
        [
            "",
            "The exact numeric arrays plotted in Figures 2–6 are stored under",
            "`figure_data` in `paper/generated/figure_manifest.json`.",
            "",
        ]
    )
    return "\n".join(lines)


def build_manifest(data: dict, outputs: list[pathlib.Path]) -> dict:
    return {
        "schema": "verified_paper_figures/1",
        "generator": rel(SCRIPT),
        "generator_sha256": sha256(SCRIPT),
        "environment": {
            "python": sys.version.split()[0],
            "matplotlib": matplotlib.__version__,
            "numpy": np.__version__,
        },
        "inputs": {
            rel(path): {
                "sha256": sha256(path),
                "source": (f"{rel(path)} (binary PNG)" if path.suffix == ".png" else span(path)),
            }
            for path in INPUT_PATHS
        },
        "figure_data": data,
        "outputs": {rel(path): sha256(path) for path in sorted(outputs)},
    }


def expected_texts(data: dict, spans: dict[str, str], manifest: dict) -> dict[pathlib.Path, str]:
    return {
        MANIFEST_PATH: json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        PROVENANCE_PATH: provenance(data, spans, manifest["outputs"]),
        CAPTIONS_PATH: captions(data, spans),
    }


def run_generate() -> int:
    data, spans = collect_data()
    outputs = generate_figures(data, FIGURES)
    manifest = build_manifest(data, outputs)
    texts = expected_texts(data, spans, manifest)
    GENERATED.mkdir(parents=True, exist_ok=True)
    for path, content in texts.items():
        path.write_text(content, encoding="utf-8", newline="\n")
    print(f"generated {len({path.stem for path in outputs})} figures; vector diagrams also include SVG")
    for path in outputs:
        print(f"  {rel(path)}")
    print(f"wrote {rel(MANIFEST_PATH)}")
    print(f"wrote {rel(PROVENANCE_PATH)}")
    print(f"wrote {rel(CAPTIONS_PATH)}")
    return 0


def run_check() -> int:
    if not MANIFEST_PATH.is_file():
        raise FigureInputError("figure manifest is missing; run without --check")
    stored = read_json(MANIFEST_PATH)
    data, spans = collect_data()
    if stored.get("generator_sha256") != sha256(SCRIPT):
        raise FigureInputError("figure generator changed after manifest creation")
    if stored.get("figure_data") != data:
        raise FigureInputError("plotted numeric arrays are stale")
    current_inputs = {rel(path): sha256(path) for path in INPUT_PATHS}
    stored_inputs = {path: row["sha256"] for path, row in stored.get("inputs", {}).items()}
    if current_inputs != stored_inputs:
        raise FigureInputError("figure input hashes are stale")
    for path_text, digest in stored.get("outputs", {}).items():
        path = ROOT / path_text
        if not path.is_file() or sha256(path) != digest:
            raise FigureInputError(f"figure output hash mismatch: {path_text}")

    with tempfile.TemporaryDirectory(prefix="verified-figures-") as tmp:
        tempdir = pathlib.Path(tmp)
        rebuilt = generate_figures(data, tempdir)
        rebuilt_by_name = {path.name: sha256(path) for path in rebuilt}
        stored_by_name = {pathlib.Path(path).name: digest for path, digest in stored["outputs"].items()}
        if rebuilt_by_name != stored_by_name:
            raise FigureInputError("freshly regenerated figures differ from the manifest")

    expected = expected_texts(data, spans, stored)
    for path, content in expected.items():
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise FigureInputError(f"stale figure metadata: {rel(path)}")
    print("OK: all registered figures reproduce exactly from the frozen artifacts")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="verify inputs, numeric arrays, metadata, and exact regenerated outputs")
    args = parser.parse_args()
    return run_check() if args.check else run_generate()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FigureInputError as exc:
        raise SystemExit(f"verified figure error: {exc}")
