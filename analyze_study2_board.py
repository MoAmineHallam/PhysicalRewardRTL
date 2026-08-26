#!/usr/bin/env python3
"""Audit and descriptively summarize the live Study 2 PYNQ-Z2 sweep.

This is deliberately not an inferential analysis.  The board subset required a
recorded correctness-feasibility amendment, and the descriptive summary was
implemented after the live result existed.  The script verifies raw traces and
provenance, then generates every board number and table used by the paper.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import statistics
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
BOARD = ROOT / "rtl" / "sealed_study2_board"
SPEC_PATH = ROOT / "study2_board_spec.json"
AMENDMENT_PATH = ROOT / "study2_board_protocol_amendment.json"
MANIFEST_PATH = BOARD / "selection_manifest.json"
SELS_PATH = BOARD / "study2_board_sels.json"
RAW_PATH = BOARD / "catalog_fmax.json"
BIT_PATH = BOARD / "out" / "system_study2_board.bit"
HWH_PATH = BOARD / "out" / "system_study2_board.hwh"
OUTPUT_PATH = ROOT / "study2_board_results.json"
GENERATED = ROOT / "paper" / "generated"
FAMILY_ORDER = ("fir", "firr", "poly", "iir", "med")
FAMILY_CLAIMS = {
    "fir": "Fir",
    "firr": "Firr",
    "poly": "Poly",
    "iir": "Iir",
    "med": "Med",
}


class BoardAnalysisError(RuntimeError):
    pass


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: pathlib.Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise BoardAnalysisError(f"cannot read valid JSON {rel(path)}: {exc}") from exc


def span(path: pathlib.Path) -> str:
    lines = len(path.read_text(encoding="utf-8").splitlines())
    return f"{rel(path)}:1-{lines}"


def recompute_trace(row: dict, threshold: float) -> tuple[float | None, float | None]:
    fmax = None
    first_fail = None
    failed = False
    for frequency, score in row.get("rows", []):
        if score >= threshold and not failed:
            fmax = frequency
        elif score < threshold and not failed:
            failed = True
            first_fail = frequency
        elif score >= threshold:
            raise BoardAnalysisError("a raw trace returned to passing after first failure")
    return fmax, first_fail


def verify_and_summarize() -> tuple[dict, collections.OrderedDict[str, dict]]:
    spec = read_json(SPEC_PATH)
    amendment = read_json(AMENDMENT_PATH)
    manifest = read_json(MANIFEST_PATH)
    sels = read_json(SELS_PATH)
    raw = read_json(RAW_PATH)
    if spec.get("schema") != "study2_board_spec/1":
        raise BoardAnalysisError("unexpected board specification schema")
    if amendment.get("schema") != "study2_board_protocol_amendment/1":
        raise BoardAnalysisError("unexpected protocol-amendment schema")
    if manifest.get("schema") != "study2_board_selection/1":
        raise BoardAnalysisError("unexpected selection-manifest schema")
    if raw.get("schema_version") != 2 or raw.get("measurement_kind") != "live_pynq_clock_sweep":
        raise BoardAnalysisError("reserved result is not a schema-2 live PYNQ sweep")
    if manifest.get("protocol_amendment_sha256") != sha256(AMENDMENT_PATH):
        raise BoardAnalysisError("selection manifest is detached from the amendment record")
    expected_hashes = {
        "bitstream_sha256": sha256(BIT_PATH),
        "hwh_sha256": sha256(HWH_PATH),
        "sels_sha256": sha256(SELS_PATH),
        "selection_manifest_sha256": sha256(MANIFEST_PATH),
    }
    for key, expected in expected_hashes.items():
        if raw.get("provenance", {}).get(key) != expected:
            raise BoardAnalysisError(f"live-result provenance mismatch: {key}")
    if raw.get("sels") != sels:
        raise BoardAnalysisError("live-result selector map differs from the sealed selector file")

    measurement = spec["measurement"]
    args = raw.get("args", {})
    expected_args = {
        "lo": measurement["lo_mhz"],
        "hi": measurement["hi_mhz"],
        "step": measurement["step_mhz"],
        "runs": measurement["runs"],
        "depth": measurement["depth"],
        "n_score": measurement["n_score"],
        "max_shift": measurement["max_shift"],
        "threshold": measurement["similarity_threshold"],
        "canary_margin": measurement["canary_margin_mhz"],
    }
    for key, expected in expected_args.items():
        if args.get(key) != expected:
            raise BoardAnalysisError(f"live sweep changed frozen argument {key}")
    runs = raw.get("raw_runs", [])
    if len(runs) != measurement["runs"]:
        raise BoardAnalysisError("live result has the wrong number of raw runs")
    expected_points = round(
        (measurement["hi_mhz"] - measurement["lo_mhz"])
        / measurement["step_mhz"]
    ) + 1
    per_entry_fmax: dict[str, list[float]] = {name: [] for name in sels}
    for run_index, run in enumerate(runs):
        if set(run) != set(sels):
            raise BoardAnalysisError(f"run {run_index} has the wrong selector universe")
        for name, row in run.items():
            if len(row.get("rows", [])) != expected_points:
                raise BoardAnalysisError(f"{name} run {run_index} has wrong point count")
            fmax, first_fail = recompute_trace(row, measurement["similarity_threshold"])
            if fmax != row.get("fmax") or first_fail != row.get("first_fail"):
                raise BoardAnalysisError(f"raw Fmax boundary mismatch for {name} run {run_index}")
            if fmax is None:
                raise BoardAnalysisError(f"{name} never passed in the frozen sweep range")
            per_entry_fmax[name].append(float(fmax))

    table = raw.get("table", {})
    canary_name = next(name for name, meta in sels.items() if meta["role"] == "canary")
    canary = statistics.median(per_entry_fmax[canary_name])
    if canary != raw.get("canary_median"):
        raise BoardAnalysisError("canary median does not reproduce")
    for name, values in per_entry_fmax.items():
        median = statistics.median(values)
        spread = max(values) - min(values)
        row = table.get(name, {})
        if median != row.get("silicon_fmax") or spread != row.get("spread"):
            raise BoardAnalysisError(f"summary table does not reproduce for {name}")
        if name == canary_name:
            expected_gate = "harness ref"
        else:
            expected_gate = (
                "OK" if canary - median >= measurement["canary_margin_mhz"]
                else "TOO CLOSE TO CANARY"
            )
        if row.get("gate") != expected_gate:
            raise BoardAnalysisError(f"canary gate does not reproduce for {name}")
    if not raw.get("summary", {}).get("all_entries_have_fmax"):
        raise BoardAnalysisError("live result is incomplete")

    paired: collections.OrderedDict[str, dict] = collections.OrderedDict()
    selections = manifest.get("selections", [])
    for family in FAMILY_ORDER:
        rows = [row for row in selections if row.get("family") == family]
        by_arm = {row["arm"]: row for row in rows}
        if set(by_arm) != {"sft", "rf"} or len(rows) != 2:
            raise BoardAnalysisError(f"missing symmetric pair for {family}")
        if by_arm["sft"]["design"] != by_arm["rf"]["design"]:
            raise BoardAnalysisError(f"design pairing mismatch for {family}")
        sft_name = by_arm["sft"]["entry"]
        rf_name = by_arm["rf"]["entry"]
        sft = float(table[sft_name]["silicon_fmax"])
        rf = float(table[rf_name]["silicon_fmax"])
        paired[family] = {
            "design": by_arm["sft"]["design"],
            "regime": by_arm["sft"]["regime"],
            "sft_entry": sft_name,
            "rf_entry": rf_name,
            "sft_fmax_mhz": sft,
            "rf_fmax_mhz": rf,
            "rf_minus_sft_mhz": rf - sft,
            "sft_spread_mhz": float(table[sft_name]["spread"]),
            "rf_spread_mhz": float(table[rf_name]["spread"]),
        }

    diffs = [row["rf_minus_sft_mhz"] for row in paired.values()]
    sft_values = [row["sft_fmax_mhz"] for row in paired.values()]
    rf_values = [row["rf_fmax_mhz"] for row in paired.values()]
    max_dut = max(sft_values + rf_values)
    summary = {
        "schema": "study2_board_results/1",
        "status": "post-observation descriptive summary; no inferential or independent-confirmatory claim",
        "primary_outcome_unchanged": spec["primary_outcome_unchanged"],
        "protocol_amended": True,
        "input_hashes": {
            "spec_sha256": sha256(SPEC_PATH),
            "amendment_sha256": sha256(AMENDMENT_PATH),
            "selection_manifest_sha256": sha256(MANIFEST_PATH),
            "raw_live_result_sha256": sha256(RAW_PATH),
            **expected_hashes,
        },
        "measurement": measurement,
        "raw_integrity": {
            "runs": len(runs),
            "frequency_points_per_entry_run": expected_points,
            "all_boundaries_recomputed": True,
            "no_pass_after_first_failure": True,
            "all_entry_fmax_spreads_mhz": {
                name: max(values) - min(values)
                for name, values in per_entry_fmax.items()
            },
        },
        "canary": {
            "entry": canary_name,
            "median_fmax_mhz": canary,
            "minimum_canary_margin_mhz": canary - max_dut,
            "all_dut_gates_ok": all(
                table[name]["gate"] == "OK"
                for name, meta in sels.items() if meta["role"] == "dut"
            ),
        },
        "pairs": paired,
        "descriptive_aggregate": {
            "n_pairs": len(paired),
            "sft_mean_mhz": statistics.mean(sft_values),
            "rf_mean_mhz": statistics.mean(rf_values),
            "mean_paired_difference_mhz": statistics.mean(diffs),
            "median_paired_difference_mhz": statistics.median(diffs),
            "rf_wins": sum(value > 0 for value in diffs),
            "ties": sum(value == 0 for value in diffs),
            "rf_losses": sum(value < 0 for value in diffs),
            "interpretation": "Heterogeneous descriptive support: two large RF wins, two exact ties, and one RF loss; no five-pair population inference.",
        },
    }
    return summary, paired


class Claims:
    def __init__(self) -> None:
        self.rows: collections.OrderedDict[str, dict] = collections.OrderedDict()

    def add(self, key: str, value: Any, display: str, unit: str, method: str) -> None:
        if not key.isalpha() or key in self.rows:
            raise BoardAnalysisError(f"invalid or duplicate board claim ID: {key}")
        self.rows[key] = {
            "value": value,
            "display": display,
            "unit": unit,
            "method": method,
            "sources": [span(RAW_PATH), span(MANIFEST_PATH), span(AMENDMENT_PATH)],
        }


def fmt(value: float, signed: bool = False) -> str:
    return f"{value:+.1f}" if signed else f"{value:.1f}"


def build_claims(summary: dict, paired: collections.OrderedDict[str, dict]) -> Claims:
    claims = Claims()
    agg = summary["descriptive_aggregate"]
    canary = summary["canary"]
    claims.add("BoardPairCount", agg["n_pairs"], str(agg["n_pairs"]), "pairs",
               "Count frozen within-design SFT/RF board pairs.")
    claims.add("BoardRunCount", summary["raw_integrity"]["runs"],
               str(summary["raw_integrity"]["runs"]), "runs",
               "Count repeated full live-board sweeps.")
    claims.add("BoardCanaryFmax", canary["median_fmax_mhz"],
               fmt(canary["median_fmax_mhz"]), "MHz",
               "Median live echo-canary Fmax over repeated sweeps.")
    claims.add("BoardMinimumCanaryMargin", canary["minimum_canary_margin_mhz"],
               fmt(canary["minimum_canary_margin_mhz"]), "MHz",
               "Canary median minus the maximum DUT median Fmax.")
    claims.add("BoardMaximumSpread", max(
        summary["raw_integrity"]["all_entry_fmax_spreads_mhz"].values()),
        fmt(max(summary["raw_integrity"]["all_entry_fmax_spreads_mhz"].values())),
        "MHz", "Maximum within-entry Fmax range across the repeated sweeps.")
    for name, value, label in (
        ("BoardRfWins", agg["rf_wins"], "RF wins"),
        ("BoardTies", agg["ties"], "ties"),
        ("BoardRfLosses", agg["rf_losses"], "RF losses"),
    ):
        claims.add(name, value, str(value), "pairs", f"Count descriptive {label}.")
    claims.add("BoardSftMean", agg["sft_mean_mhz"], fmt(agg["sft_mean_mhz"]),
               "MHz", "Unweighted descriptive mean across the five selected SFT DUTs.")
    claims.add("BoardRfMean", agg["rf_mean_mhz"], fmt(agg["rf_mean_mhz"]),
               "MHz", "Unweighted descriptive mean across the five selected RF DUTs.")
    claims.add("BoardMeanDifference", agg["mean_paired_difference_mhz"],
               fmt(agg["mean_paired_difference_mhz"], signed=True), "MHz",
               "Descriptive mean of the five within-design RF-minus-SFT differences; no CI or population inference.")
    claims.add("BoardMedianDifference", agg["median_paired_difference_mhz"],
               fmt(agg["median_paired_difference_mhz"], signed=True), "MHz",
               "Descriptive median of the five within-design RF-minus-SFT differences.")
    for family, row in paired.items():
        prefix = "Board" + FAMILY_CLAIMS[family]
        claims.add(prefix + "Sft", row["sft_fmax_mhz"], fmt(row["sft_fmax_mhz"]),
                   "MHz", f"Median live SFT Fmax for the selected {family} pair.")
        claims.add(prefix + "Rf", row["rf_fmax_mhz"], fmt(row["rf_fmax_mhz"]),
                   "MHz", f"Median live RF Fmax for the selected {family} pair.")
        claims.add(prefix + "Difference", row["rf_minus_sft_mhz"],
                   fmt(row["rf_minus_sft_mhz"], signed=True), "MHz",
                   f"Within-design live RF-minus-SFT difference for the selected {family} pair.")
    return claims


def tex_claims(claims: Claims) -> str:
    lines = [
        "% AUTO-GENERATED by analyze_study2_board.py. DO NOT EDIT.",
        "% Descriptive post-amendment silicon claims only; no population inference.",
        r"\providecommand{\boardclaim}[1]{\csname BoardClaim#1\endcsname}",
        "",
    ]
    for key, row in claims.rows.items():
        lines.append(f"% CLAIM {key}: {row['unit']}; {row['method']}")
        for source in row["sources"]:
            lines.append(f"% SOURCE {source}")
        lines.append(
            rf"\expandafter\def\csname BoardClaim{key}\endcsname{{{row['display']}}}"
        )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def tex_table(paired: collections.OrderedDict[str, dict]) -> str:
    rows = []
    for family, row in paired.items():
        prefix = "Board" + FAMILY_CLAIMS[family]
        rows.append(
            f"{family.upper()} & {row['design'].replace('_', r'\_')} & "
            f"\\boardclaim{{{prefix}Sft}} & \\boardclaim{{{prefix}Rf}} & "
            f"\\boardclaim{{{prefix}Difference}} \\\\"
        )
    body = "\n".join(rows)
    return rf"""% AUTO-GENERATED by analyze_study2_board.py. DO NOT EDIT.
\begin{{table}}[t]
\centering
\caption{{Descriptive PYNQ-Z2 clock-sweep confirmation on
\boardclaim{{BoardPairCount}} paired designs. Values are medians over
\boardclaim{{BoardRunCount}} repeated sweeps. The subset required a disclosed
correctness-feasibility amendment and is not independent confirmatory evidence.}}
\label{{tab:study2-board}}
\small
\begin{{tabular}}{{llrrr}}
\toprule
Family & Design & SFT & RF & RF--SFT [MHz] \\
\midrule
{body}
\bottomrule
\end{{tabular}}
\end{{table}}
"""


def provenance_markdown(claims: Claims) -> str:
    lines = [
        "# Study 2 board claim provenance",
        "",
        "Generated by `analyze_study2_board.py`; descriptive post-amendment silicon only.",
        "",
        "| Claim | Display | Unit | Sources |",
        "|---|---:|---|---|",
    ]
    for key, row in claims.rows.items():
        lines.append(
            f"| `{key}` | {row['display']} | {row['unit']} | "
            + "<br>".join(f"`{source}`" for source in row["sources"])
            + " |"
        )
    return "\n".join(lines) + "\n"


def render() -> tuple[dict[pathlib.Path, str], dict]:
    summary, paired = verify_and_summarize()
    claims = build_claims(summary, paired)
    ledger = {
        "schema": 1,
        "generator": "analyze_study2_board.py",
        "status": summary["status"],
        "claims": claims.rows,
    }
    outputs = {
        OUTPUT_PATH: json.dumps(summary, indent=2) + "\n",
        GENERATED / "study2_board_claims.json": json.dumps(ledger, indent=2) + "\n",
        GENERATED / "study2_board_claims.tex": tex_claims(claims),
        GENERATED / "study2_board_claim_provenance.md": provenance_markdown(claims),
        GENERATED / "study2_table_board.tex": tex_table(paired),
    }
    return outputs, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated outputs are stale")
    args = parser.parse_args()
    outputs, summary = render()
    if args.check:
        stale = [
            rel(path) for path, content in outputs.items()
            if not path.is_file() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            print("stale Study 2 board outputs: " + ", ".join(stale))
            return 1
        print("Study 2 board outputs are current and raw provenance reproduces")
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
        agg = summary["descriptive_aggregate"]
        print(
            f"Study 2 board: {agg['rf_wins']} RF wins, {agg['ties']} ties, "
            f"{agg['rf_losses']} loss; mean paired difference "
            f"{agg['mean_paired_difference_mhz']:+.3f} MHz"
        )
        print("Status: descriptive post-amendment support; no population inference")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
