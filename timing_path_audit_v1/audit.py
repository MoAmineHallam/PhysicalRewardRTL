"""Read existing Study-2 artifacts; never run EDA or modify frozen outcomes.

The only writable outputs are this directory's audit.json and REPORT.md.
Zero-slack cases are suspects, not confirmed missing-path events. Nonzero
slack excludes the specific zero-default branch, not all constraint defects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verify_sealed_ppa import sha256_file, verify_directory

HERE = Path(__file__).resolve().parent
ARM_DIRS = {
    "sft": ["sealed_sft"],
    "rf": ["sealed_rf_s1", "sealed_rf_s2"],
    "mlp": ["sealed_mlp_s1", "sealed_mlp_s2"],
    "correctness": ["sealed_corr_s1"],
}


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def build():
    frozen = read("sealed_ppa_audit_study2.json")
    primary = read("sealed_results_study2.json")
    designs = primary["designs"]
    period = frozen["period_ns"]
    if period != 5.0 or len(designs) != 20:
        raise ValueError("Unexpected frozen endpoint or design universe")
    for filename, key in (("ppa_synth.tcl", "ppa_tcl_sha256"),
                          ("run_ppa.py", "run_ppa_sha256")):
        if sha256_file(str(ROOT / filename)) != frozen[key]:
            raise ValueError(f"Frozen measurement source changed: {filename}")

    inputs = {}

    def bind(path):
        path = Path(path)
        inputs[path.relative_to(ROOT).as_posix()] = sha256_file(str(path))

    for name in ("ppa_synth.tcl", "run_ppa.py", "sealed_ppa_audit_study2.json",
                 "sealed_results_study2.json", "verify_sealed_ppa.py"):
        bind(ROOT / name)
    bind(Path(__file__).resolve())
    all_rows, directory_summary, by_dir = [], [], {}
    for expected in frozen["directories"]:
        # Resolve only named frozen study directories inside this repository.
        name = expected["directory"].replace("\\", "/").rsplit("/", 1)[1]
        directory = ROOT / "rtl" / name
        actual = verify_directory(str(directory))
        for key in ("manifest_sha256", "ppa_sha256", "n_candidates",
                    "n_compiled", "n_failed"):
            if actual[key] != expected[key]:
                raise ValueError(f"Frozen artifact mismatch: {name}/{key}")
        manifest = read(directory / "fmax_manifest.json")
        bind(directory / "fmax_manifest.json")
        bind(directory / "ppa.jsonl")
        records = []
        for lineno, line in enumerate((directory / "ppa.jsonl").read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            ppa = json.loads(line)
            meta = manifest[ppa["module"]]
            rtl = directory / (ppa["module"] + ".sv")
            bind(rtl)
            if sha256_file(str(rtl)) != meta["emitted_sha256"]:
                raise ValueError(f"Emitted RTL hash mismatch: {rtl}")
            row = dict(directory=name, module=ppa["module"], design=meta["design"],
                       count=meta["count"], draw_budget=meta["n"],
                       source=f"{(directory / 'ppa.jsonl').relative_to(ROOT).as_posix()}:{lineno}",
                       rtl=rtl.relative_to(ROOT).as_posix(), measurement=ppa)
            if ppa["compiled"]:
                slack = float(ppa["wns"])
                achieved = period - slack
                calc = 1000 / achieved if achieved > 0 else 0
                if not math.isfinite(slack) or not math.isclose(calc, ppa["fmax_mhz"], rel_tol=1e-12, abs_tol=1e-12):
                    raise ValueError(f"Invalid slack/frequency arithmetic: {ppa['module']}")
                row["zero_slack_suspect"] = slack == 0
                row["zero_counted_resources"] = all(ppa[k] == 0 for k in ("lut", "ff", "dsp", "bram"))
                row["interpretation"] = ("zero-default-compatible; replay needed" if slack == 0
                                         else "nonzero recorded slack excludes the unchanged zero default")
            else:
                row.update(zero_slack_suspect=False, zero_counted_resources=False,
                           interpretation="explicit implementation failure; already zero-scored")
            records.append(row)
        reports = sorted(p.relative_to(ROOT).as_posix() for p in directory.rglob("*")
                         if p.is_file() and p.suffix.lower() in {".rpt", ".dcp", ".log", ".xdc"})
        by_dir[name] = records
        all_rows.extend(records)
        directory_summary.append(dict(directory=name, candidates=len(records),
                                      compiled=sum(bool(r["measurement"]["compiled"]) for r in records),
                                      zero_slack_suspects=sum(r["zero_slack_suspect"] for r in records),
                                      retained_reports=reports))

    # Reconstruct the original estimand, including missing/failed draws as zero.
    # The diagnostic scenario sets suspect timing values to zero; no draw is removed.
    effects, endpoint = {}, {}
    for arm, names in ARM_DIRS.items():
        saved = primary["sft"] if arm == "sft" else primary["arms"][arm]
        original, scenario = {}, {}
        for design in designs:
            original[design] = scenario[design] = 0.0
            for name in names:
                rows = [r for r in by_dir[name] if r["design"] == design]
                for row in rows:
                    f = row["measurement"].get("fmax_mhz", 0) if row["measurement"]["compiled"] else 0
                    contribution = row["count"] / row["draw_budget"] * f / len(names)
                    original[design] += contribution
                    if not row["zero_slack_suspect"]:
                        scenario[design] += contribution
            if not math.isclose(original[design], saved[design]["equal"], abs_tol=1e-9):
                raise ValueError(f"Primary reconstruction mismatch: {arm}/{design}")
        endpoint[arm] = dict(original_mean=sum(original.values()) / len(designs),
                             zero_suspects_mean=sum(scenario.values()) / len(designs),
                             original_by_design=original, zero_suspects_by_design=scenario)
    for name, subset in (("all", designs), ("median_family", ["med19", "med21"])):
        effects[name] = {
            kind: sum(endpoint["rf"][kind][d] - endpoint["sft"][kind][d] for d in subset) / len(subset)
            for kind in ("original_by_design", "zero_suspects_by_design")
        }
    suspects = [r for r in all_rows if r["zero_slack_suspect"]]
    return dict(schema="study2_read_only_timing_audit/1", input_sha256_lf=inputs,
                scope="existing artifacts only; no GPU/EDA runs; frozen results unchanged",
                total_candidates=len(all_rows), compiled=sum(bool(r["measurement"]["compiled"]) for r in all_rows),
                primary_sft_rf_candidates=sum(len(by_dir[n]) for a in ("sft", "rf") for n in ARM_DIRS[a]),
                directories=directory_summary, suspects=suspects, rows=all_rows,
                endpoints=endpoint, rf_minus_sft_diagnostics=effects,
                timing_coverage_verified=False, fallback_occurrence_confirmed=False,
                limitations=["Original runner suppressed Vivado journal/log and discarded successful stdout.",
                             "No retained per-candidate timing/constraint report was found in the audited sealed directories.",
                             "Nonzero slack demonstrates a numeric reported path under the bound script, not complete constraint coverage.",
                             "Zero slack alone could be genuine; the zero-resource suspect requires instrumented replay.",
                             "The zero-score scenario is diagnostic, not an adjudicated correction or a new confidence interval."])


def report(a):
    lines = ["# Read-only Study-2 timing audit — 2026-09-05", "",
             "## Outcome", "",
             f"Audited {a['total_candidates']} frozen candidate rows: {a['compiled']} compiled and "
             f"{a['total_candidates'] - a['compiled']} explicit implementation failure. "
             f"The primary SFT/RF comparison contains {a['primary_sft_rf_candidates']} candidate rows.", "",
             "Frozen measurement-script, runner, manifest, PPA, and emitted-RTL hashes were checked. "
             "All four endpoint-arm means were independently reconstructed without changing any outcome.", "",
             "| Directory | Candidates | Compiled | Zero-slack suspects |",
             "|---|---:|---:|---:|"]
    for d in a["directories"]:
        lines.append(f"| {d['directory']} | {d['candidates']} | {d['compiled']} | {d['zero_slack_suspects']} |")
    lines += ["", "## Suspect and exact scope of inference", "",
              "The frozen Tcl initializes slack to zero and replaces it only when a setup path returns "
              "numeric slack. An unchanged default therefore yields 200 MHz at the frozen 5 ns request. "
              "Its comment claiming a missing path scores zero frequency contradicts the executed formula.", ""]
    for r in a["suspects"]:
        lines += [f"- `{r['module']}` ({r['source']}): {r['count']}/{r['draw_budget']} draws for "
                  f"{r['design']}; recorded slack {r['measurement']['wns']} ns and "
                  f"frequency {r['measurement']['fmax_mhz']} MHz; zero LUT/FF/DSP/BRAM counts: "
                  f"{r['zero_counted_resources']}."]
    lines += ["", "The suspect's RTL assigns `y` in both combinational and clocked processes. "
              "This is a plausible synthesis/simulation mismatch mechanism, not a confirmed diagnosis "
              "without the original netlist or an instrumented replay.", "",
              "Every other compiled row has nonzero finite slack and consistent frequency arithmetic. "
              "Thus none can have been scored by the unchanged zero-default branch, assuming the "
              "hash-bound script and retained row are the measurement authority. This does not certify "
              "clock coverage, complete routing, hold/pulse timing, or synthesized functionality.", "",
              "## Diagnostic sensitivity only", "",
              "Set the suspect's physical score to zero while retaining its draw in the denominator. "
              "This is not yet a correction to the manuscript or its original confidence interval.", "",
              "| Quantity | Frozen result (MHz) | Zero-suspect scenario (MHz) |",
              "|---|---:|---:|"]
    for arm in ("sft", "rf"):
        e = a["endpoints"][arm]
        lines.append(f"| {arm.upper()} overall | {e['original_mean']:.6f} | {e['zero_suspects_mean']:.6f} |")
    for label, name in (("RF minus SFT overall", "all"), ("RF minus SFT median-family mean", "median_family")):
        e = a["rf_minus_sft_diagnostics"][name]
        lines.append(f"| {label} | {e['original_by_design']:.6f} | {e['zero_suspects_by_design']:.6f} |")
    lines += ["", "## What remains", "",
              "- No original per-candidate timing/constraint reports or checkpoints were retained in "
              "the eight sealed directories. The aggregate launcher log cannot establish path coverage.",
              "- First replay only the flagged SFT candidate with diagnostics that retain synthesis "
              "warnings, resource counts, clocks, setup-path count, constraints, routed netlist/checkpoint, "
              "and timing reports. Preserve the original RTL, part, 5 ns request, and constraint order.",
              "- Vivado 2023.1 is installed but the repository records later runtime instability on "
              "this Windows host. A 2026.1 replay must be labeled cross-version diagnostic, not an exact "
              "reproduction or retroactive replacement of a 2023.1 observation.",
              "- Freeze any broader coverage/closure diagnostic before launching it; include both arms "
              "and preserve failure/multiplicity accounting. Do not silently rerun only favorable cases.",
              "- If an invalid physical score is confirmed, publish an explicit correction and propagate "
              "it through affected analyses. Preserve the original version as historical evidence.", "",
              "No GPU jobs, Vivado processes, original results, manuscript files, or GitHub state were changed.", "",
              "Reproduce with `python timing_path_audit_v1/audit.py --check`. "
              "JSON includes per-candidate findings and LF-normalized source hashes.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    a = build()
    outputs = {HERE / "audit.json": json.dumps(a, indent=2) + "\n", HERE / "REPORT.md": report(a)}
    for path, text in outputs.items():
        if args.check:
            if path.read_text(encoding="utf-8") != text:
                raise ValueError(f"Stale audit output: {path}")
        else:
            path.write_text(text, encoding="utf-8", newline="\n")
    print(f"PASS read-only audit: {a['total_candidates']} rows, {len(a['suspects'])} zero-slack suspect(s)")
    print(json.dumps(a["rf_minus_sft_diagnostics"], indent=2))


if __name__ == "__main__":
    main()
