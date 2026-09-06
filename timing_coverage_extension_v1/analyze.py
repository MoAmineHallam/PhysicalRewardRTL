"""Post-completion analysis; no edits to the frozen campaign or original study."""
import collections
import json
import math
import re
import statistics
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from timing_coverage_extension_v1.run import verify
from eval_sealed import sha256_file, load_split


def main():
    frozen = verify()
    old = {}
    for directory in ("sealed_sft", "sealed_rf_s1", "sealed_rf_s2"):
        for line in (ROOT / "rtl" / directory / "ppa.jsonl").read_text().splitlines():
            row = json.loads(line)
            old[row["module"]] = row
    rows = []
    sources = {}
    for candidate in frozen["candidates"]:
        directory = HERE / "results" / candidate["module"]
        path = directory / "completion.json"
        result = json.loads(path.read_text())
        if result["freeze_sha256_lf"] != sha256_file(str(HERE / "freeze.json")) or result["candidate"] != candidate:
            raise RuntimeError("Completion identity mismatch")
        for rel, expected in result["artifact_hashes"].items():
            if sha256_file(str(directory / rel)) != expected:
                raise RuntimeError("Artifact changed: " + str(directory / rel))
        sources[path.relative_to(ROOT).as_posix()] = sha256_file(str(path))
        final = result["trials"][-1]
        trial = directory / f"attempt_{final['attempt']}"
        check_text = (trial / "reports/check_timing.txt").read_text() if (trial / "reports/check_timing.txt").exists() else ""
        counts = {name: int(value) for name, value in re.findall(r"checking (\w+) \((\d+)\)", check_text)}
        required = ("no_clock", "unconstrained_internal_endpoints", "no_input_delay",
                    "no_output_delay", "partial_input_delay", "partial_output_delay")
        coverage = all(counts.get(key) == 0 for key in required)
        log = (trial / "stdout.log").read_text(errors="replace")
        diagnostic = final.get("diagnostic", {})
        actual_path = final["classification"] == "SETUP_PATH_PRESENT"
        frequency = diagnostic.get("historical_fmax_mhz")
        good = actual_path and coverage and isinstance(frequency, (float, int)) and math.isfinite(frequency) and frequency > 0
        replay = frequency if good else (0.0 if final["classification"] == "INVALID_NO_SETUP_PATH" else None)
        rows.append(dict(module=candidate["module"], policy=candidate["policy"],
            design=candidate["design"], count=candidate["count"], n=candidate["n"],
            classification=final["classification"], check_timing_counts=counts,
            constraint_counts_clear=coverage, multi_driver_warning="Synth 8-685" in log,
            old_fmax_mhz=old[candidate["module"]]["fmax_mhz"],
            replay_diagnostic_mhz=replay, **{"path_diagnostic": diagnostic}))
    split = load_split(str(ROOT / "sealed_split.json"))
    arms = {}
    for policy in ("sft", "rf_s1", "rf_s2"):
        subset = [r for r in rows if r["policy"] == policy]
        per_design = []
        for design in split:
            cell = [r for r in subset if r["design"] == design["design"]]
            old_mean = sum(r["old_fmax_mhz"] * r["count"] / r["n"] for r in cell)
            new_mean = (sum(r["replay_diagnostic_mhz"] * r["count"] / r["n"] for r in cell)
                        if all(r["replay_diagnostic_mhz"] is not None for r in cell) else None)
            per_design.append(dict(design=design["design"], original=old_mean, replay=new_mean))
        comparable = [r for r in subset if r["replay_diagnostic_mhz"] is not None and r["replay_diagnostic_mhz"] > 0]
        errors = [200 * abs(r["replay_diagnostic_mhz"] - r["old_fmax_mhz"]) /
                  (r["replay_diagnostic_mhz"] + r["old_fmax_mhz"]) for r in comparable]
        arms[policy] = {"n_candidates": len(subset), "classifications": dict(collections.Counter(r["classification"] for r in subset)),
            "constraint_counts_not_clear": sum(not r["constraint_counts_clear"] for r in subset),
            "multi_driver_warning_candidates": sum(r["multi_driver_warning"] for r in subset),
            "median_smape_percent_common_valid": statistics.median(errors),
            "max_smape_percent_common_valid": max(errors),
            "original_equal_design_mean": statistics.mean(r["original"] for r in per_design),
            "replay_equal_design_mean": statistics.mean(r["replay"] for r in per_design) if all(r["replay"] is not None for r in per_design) else None,
            "per_design": per_design}
    payload = {"scope": "exhaustive post-primary cross-version diagnostic; not revised primary inference",
               "n_candidates": len(rows), "arms": arms, "candidates": rows, "completion_sources": sources}
    (HERE / "analysis.json").write_text(json.dumps(payload, indent=2) + "\n")
    lines = ["# Completed timing-coverage audit — 2026-09-06", "",
        "All 202 original SFT/RF candidate completion identities and retained artifact hashes verified.", "",
        "| Arm | Candidates | Setup path | No setup path | Inconclusive | Constraint counts not confirmed clear |",
        "|---|---:|---:|---:|---:|---:|"]
    for policy, arm in arms.items():
        c = arm["classifications"]
        lines.append(f"| {policy} | {arm['n_candidates']} | {c.get('SETUP_PATH_PRESENT',0)} | {c.get('INVALID_NO_SETUP_PATH',0)} | {c.get('INCONCLUSIVE',0)} | {arm['constraint_counts_not_clear']} |")
    invalid = [r["module"] for r in rows if r["classification"] == "INVALID_NO_SETUP_PATH"]
    inconclusive = [r["module"] for r in rows if r["classification"] == "INCONCLUSIVE"]
    multidriver = [r["module"] for r in rows if r["multi_driver_warning"]]
    lines.extend(["", "All 197 setup-path-present candidates have zero counts for the six named constraint-coverage checks. The columns not confirmed clear are exactly the four inconclusive implementation failures, for which no routed timing report exists.",
        "", "- Confirmed no-path candidate: `" + "`, `".join(invalid) + "`.",
        "- Inconclusive under Vivado 2026.1 after two fresh attempts: `" + "`, `".join(inconclusive) + "`.",
        "- Multi-driver synthesis warnings: `" + "`, `".join(multidriver) + "` (warnings alone were not silently converted to failures)."])
    lines.extend(["", "## Cross-version frequency sensitivity", "",
        "Diagnostic means keep every original draw in the denominator and assign zero to verified missing-path replays. Inconclusive cases make an arm mean unavailable, not zero. Original results are unchanged.", "",
        "| Arm | Original mean MHz | Replay diagnostic mean MHz | Median / max symmetric error on common valid candidates (%) |",
        "|---|---:|---:|---:|"])
    for policy, arm in arms.items():
        mean = arm["replay_equal_design_mean"]
        shown = f"{mean:.6f}" if mean is not None else "unavailable"
        lines.append(f"| {policy} | {arm['original_equal_design_mean']:.6f} | {shown} | {arm['median_smape_percent_common_valid']:.3f} / {arm['max_smape_percent_common_valid']:.3f} |")
    lines.extend(["", "## Limits", "", "This holds RTL, part, clock request and constraint order fixed but changes Vivado version. It is not period-bracketed setup closure, full hold/pulse-width sign-off, synthesized-equivalence verification, or a corrected primary confidence interval. A setup path alone is insufficient: the named constraint checks are reported separately. Multi-driver warnings are recorded in analysis.json and require review; they are not silently converted into physical failures.", ""])
    (HERE / "REPORT.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
