"""One cross-version diagnostic; never updates historical PPA or paper results."""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from timing_closure_candidate_v7.run_candidates import dependency_guard
from timing_closure_candidate_v7.common import BASELINE, verify_v7_pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", required=True, choices=["02"])
    parser.add_argument("--scratch", type=Path, required=True)
    args = parser.parse_args()
    output = ROOT / ("timing_path_audit_v1/replay_20260905_" + args.attempt)
    output.mkdir(exist_ok=False)
    args.scratch.mkdir(exist_ok=False)
    for name in ("work", "temp"):
        (args.scratch / name).mkdir()
    (output / "reports").mkdir()
    verify_v7_pass()
    baseline = json.loads(BASELINE.read_text())
    before = dependency_guard(baseline)
    if not before[0]:
        raise RuntimeError(before[2])
    rtl = ROOT / "rtl/sealed_sft/sft__med21__g3.sv"
    digest = hashlib.sha256(rtl.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if digest != "f4d94de502bab3391d3f47163feff2253da6b3c74ffca92eb5d5ebde14a23422":
        raise RuntimeError("Frozen RTL changed")
    command = [r"C:\AMD\2026.1\Vivado\bin\vivado.bat", "-mode", "batch",
               "-nojournal", "-nolog", "-notrace", "-tempDir", str(args.scratch / "temp"),
               "-source", str(ROOT / "timing_path_audit_v1/replay.tcl"),
               "-tclargs", str(rtl), "sft__med21__g3", "clk", "5.0",
               str(output / "historical_formula.json"), str(ROOT / "ppa_synth.tcl"),
               str(output / "reports")]
    record = {"scope": "single flagged SFT candidate; cross-version diagnostic, not historical replacement",
              "started_utc": datetime.now(timezone.utc).isoformat(),
              "command": command, "rtl_sha256_lf": digest, "dependency_before": before,
              "inputs_sha256_lf": {p: hashlib.sha256((ROOT / p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                  for p in ("ppa_synth.tcl", "timing_path_audit_v1/replay.tcl", "timing_path_audit_v1/replay.py")}}
    (output / "launch.json").write_text(json.dumps(record, indent=2) + "\n")
    with (output / "stdout.log").open("w") as stdout, (output / "stderr.log").open("w") as stderr:
        try:
            result = subprocess.run(subprocess.list2cmdline(command), shell=True,
                cwd=args.scratch / "work", stdout=stdout, stderr=stderr, timeout=1800)
            record["returncode"] = result.returncode
        except subprocess.TimeoutExpired:
            record["error"] = "timeout; inspect child processes before any retry"
            raise
        finally:
            record["dependency_after"] = dependency_guard(baseline)
            record["ended_utc"] = datetime.now(timezone.utc).isoformat()
            (output / "completion.json").write_text(json.dumps(record, indent=2) + "\n")
    if result.returncode or not record["dependency_after"][0]:
        raise RuntimeError("Diagnostic failed; inspect retained outputs")
    print((output / "reports/path_diagnostic.json").read_text())


if __name__ == "__main__":
    main()
