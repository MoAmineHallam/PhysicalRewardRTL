#!/usr/bin/env python3
"""Fresh-period bracketing and bisection for timing_closure_gate_v1."""

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

try:
    from . import generate_manifest as gm
except ImportError:  # direct script execution
    import generate_manifest as gm


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TCL = HERE / "closure_synth.tcl"
DEFAULT_RESULTS = HERE / "results"
PART = "xc7z020clg400-1"


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    os.replace(temp, path)


def read_manifest():
    expected = gm.build_manifest()
    digest = gm.check_frozen(expected)
    return expected, digest


def period_token(period):
    return f"{period:.9f}".rstrip("0").rstrip(".").replace(".", "p")


def initial_periods(delay_ns, floor=1.0, ceiling=200.0):
    return max(floor, 0.75 * delay_ns), min(ceiling, 1.25 * delay_ns)


def relative_bracket_width(tight_fail_ns, loose_pass_ns):
    midpoint = 0.5 * (tight_fail_ns + loose_pass_ns)
    return (loose_pass_ns - tight_fail_ns) / midpoint


def measurement_valid(record):
    required = (
        int(record.get("compiled", 0)) == 1,
        int(record.get("implemented", 0)) == 1,
        int(record.get("clock_count", 0)) == 1,
        int(record.get("setup_path_count", 0)) > 0,
        int(record.get("summary_parse_ok", 0)) == 1,
        int(record.get("unconstrained_path_count", -1)) == 0,
        int(record.get("route_clean", 0)) == 1,
        int(record.get("constraint_coverage_ok", 0)) == 1,
    )
    return all(required) and math.isfinite(float(record.get("wns_ns", math.nan)))


def monotonic_contradictions(trials, tolerance=1e-9):
    valid = [trial for trial in trials if trial.get("valid_measurement")]
    passed = [float(trial["period_ns"]) for trial in valid if trial["closed"]]
    failed = [float(trial["period_ns"]) for trial in valid if not trial["closed"]]
    return sorted((p_pass, p_fail) for p_pass in passed for p_fail in failed
                  if p_pass + tolerance < p_fail)


class TrialRunner:
    def __init__(self, vivado, candidate, manifest_digest, result_root,
                 retries=1, dry_run=False):
        self.vivado = str(vivado)
        self.candidate = candidate
        self.manifest_digest = manifest_digest
        self.candidate_dir = Path(result_root) / candidate["candidate_id"]
        self.ledger_path = self.candidate_dir / "trials.jsonl"
        self.retries = retries
        self.dry_run = dry_run
        self.trials = self._load_ledger()

    def _load_ledger(self):
        if not self.ledger_path.is_file():
            return []
        rows = []
        for lineno, line in enumerate(
                self.ledger_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("manifest_sha256") != self.manifest_digest:
                raise RuntimeError(
                    f"stale ledger manifest at {self.ledger_path}:{lineno}")
            rows.append(row)
        return rows

    def _append(self, row):
        self.candidate_dir.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8", newline="\n") as out:
            out.write(json.dumps(row, sort_keys=True) + "\n")
            out.flush()
        self.trials.append(row)

    def _cached(self, period, purpose):
        for row in reversed(self.trials):
            if (row.get("purpose") == purpose
                    and math.isclose(float(row["period_ns"]), period,
                                     rel_tol=0.0, abs_tol=5e-10)):
                return row
        return None

    def command(self, period, trial_dir):
        result_json = trial_dir / "vivado_result.json"
        reports = trial_dir / "reports"
        source = ROOT / self.candidate["materialized_path"]
        return [
            self.vivado,
            "-mode", "batch", "-nojournal", "-nolog", "-notrace",
            "-source", str(TCL), "-tclargs", str(source),
            self.candidate["module"], self.candidate["clock_port"],
            f"{period:.12g}", str(result_json), str(reports), PART,
        ]

    def run(self, period, purpose, force_fresh=False):
        period = float(period)
        if not force_fresh:
            cached = self._cached(period, purpose)
            if cached is not None:
                return cached
        last = None
        for attempt in range(self.retries + 1):
            sequence = len(self.trials) + 1
            name = (f"trial_{sequence:03d}_{purpose}_p{period_token(period)}"
                    f"_a{attempt}")
            trial_dir = self.candidate_dir / name
            command = self.command(period, trial_dir)
            if self.dry_run:
                print(subprocess.list2cmdline(command))
                return {
                    "period_ns": period,
                    "purpose": purpose,
                    "dry_run": True,
                    "valid_measurement": True,
                    "closed": False,
                }
            if trial_dir.exists():
                raise RuntimeError(f"refusing dirty trial directory: {trial_dir}")
            trial_dir.mkdir(parents=True)
            stdout_path = trial_dir / "vivado.stdout.log"
            stderr_path = trial_dir / "vivado.stderr.log"
            with stdout_path.open("w", encoding="utf-8", errors="replace") as stdout, \
                    stderr_path.open("w", encoding="utf-8", errors="replace") as stderr:
                if os.name == "nt":
                    completed = subprocess.run(
                        subprocess.list2cmdline(command), cwd=trial_dir,
                        stdout=stdout, stderr=stderr, shell=True, check=False)
                else:
                    completed = subprocess.run(
                        command, cwd=trial_dir, stdout=stdout, stderr=stderr,
                        check=False)
            result_path = trial_dir / "vivado_result.json"
            parsed = {}
            parse_error = None
            try:
                parsed = json.loads(result_path.read_text(encoding="utf-8"))
            except Exception as exc:
                parse_error = str(exc)
            valid = completed.returncode == 0 and measurement_valid(parsed)
            row = {
                "schema_version": 1,
                "manifest_sha256": self.manifest_digest,
                "candidate_id": self.candidate["candidate_id"],
                "period_ns": period,
                "purpose": purpose,
                "attempt": attempt,
                "trial_dir": trial_dir.resolve().relative_to(ROOT).as_posix(),
                "returncode": completed.returncode,
                "parse_error": parse_error,
                "valid_measurement": valid,
                "closed": bool(valid and int(parsed.get("closed", 0)) == 1),
                "vivado": parsed,
                "stdout_sha256": sha256_file(stdout_path),
                "stderr_sha256": sha256_file(stderr_path),
                "result_sha256": sha256_file(result_path)
                    if result_path.is_file() else None,
            }
            self._append(row)
            last = row
            if valid:
                return row
        return last


def fail_result(candidate, digest, trials, reason):
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v1",
        "scope": "pilot_10",
        "manifest_sha256": digest,
        "candidate_id": candidate["candidate_id"],
        "family": candidate["family"],
        "design": candidate["design"],
        "arm": candidate["arm"],
        "module": candidate["module"],
        "old_fmax_mhz": candidate["old_fmax_mhz"],
        "status": "FAILED",
        "failure_reason": reason,
        "closure_fmax_mhz": 0.0,
        "trial_count": len(trials),
        "trials": trials,
    }


def close_candidate(candidate, digest, runner, dry_run=False):
    delay = float(candidate["old_proxy_delay_ns"])
    floor, ceiling = 1.0, 200.0
    tight, loose = initial_periods(delay, floor, ceiling)
    if dry_run:
        runner.run(tight, "initial_tight")
        runner.run(loose, "initial_loose")
        return None

    tight_row = runner.run(tight, "search")
    loose_row = runner.run(loose, "search")
    if not tight_row.get("valid_measurement") or not loose_row.get("valid_measurement"):
        return fail_result(candidate, digest, runner.trials,
                           "permanent_invalid_initial_measurement")

    expansions = 0
    while tight_row["closed"] and expansions < 4 and tight > floor:
        new_tight = max(floor, tight / 1.5)
        if math.isclose(new_tight, tight):
            break
        tight = new_tight
        tight_row = runner.run(tight, "search")
        if not tight_row.get("valid_measurement"):
            return fail_result(candidate, digest, runner.trials,
                               "permanent_invalid_tight_expansion")
        expansions += 1
    if tight_row["closed"]:
        return fail_result(candidate, digest, runner.trials,
                           "no_failing_period_within_preregistered_floor")

    expansions = 0
    while not loose_row["closed"] and expansions < 4 and loose < ceiling:
        new_loose = min(ceiling, loose * 1.5)
        if math.isclose(new_loose, loose):
            break
        loose = new_loose
        loose_row = runner.run(loose, "search")
        if not loose_row.get("valid_measurement"):
            return fail_result(candidate, digest, runner.trials,
                               "permanent_invalid_loose_expansion")
        expansions += 1
    if not loose_row["closed"]:
        return fail_result(candidate, digest, runner.trials,
                           "no_passing_period_within_preregistered_ceiling")

    bisections = 0
    while relative_bracket_width(tight, loose) > 0.01 and bisections < 10:
        midpoint = 0.5 * (tight + loose)
        row = runner.run(midpoint, "search")
        if not row.get("valid_measurement"):
            return fail_result(candidate, digest, runner.trials,
                               "permanent_invalid_bisection_measurement")
        if row["closed"]:
            loose, loose_row = midpoint, row
        else:
            tight, tight_row = midpoint, row
        bisections += 1
    if relative_bracket_width(tight, loose) > 0.01:
        return fail_result(candidate, digest, runner.trials,
                           "bisection_tolerance_not_reached")

    contradictions = monotonic_contradictions(runner.trials)
    if contradictions:
        return fail_result(candidate, digest, runner.trials,
                           f"nonmonotonic_search:{contradictions}")

    confirm_fail = runner.run(tight, "confirm_fail", force_fresh=True)
    confirm_pass = runner.run(loose, "confirm_pass", force_fresh=True)
    if (not confirm_fail.get("valid_measurement")
            or not confirm_pass.get("valid_measurement")):
        return fail_result(candidate, digest, runner.trials,
                           "permanent_invalid_boundary_confirmation")
    if confirm_fail["closed"] or not confirm_pass["closed"]:
        return fail_result(candidate, digest, runner.trials,
                           "nondeterministic_boundary_confirmation")

    closure = 1000.0 / loose
    upper = 1000.0 / tight
    return {
        "schema_version": 1,
        "study_id": "timing_closure_gate_v1",
        "scope": "pilot_10",
        "manifest_sha256": digest,
        "candidate_id": candidate["candidate_id"],
        "family": candidate["family"],
        "design": candidate["design"],
        "arm": candidate["arm"],
        "module": candidate["module"],
        "old_fmax_mhz": candidate["old_fmax_mhz"],
        "status": "COMPLETE",
        "failure_reason": None,
        "tight_failing_period_ns": tight,
        "loose_passing_period_ns": loose,
        "relative_bracket_width": relative_bracket_width(tight, loose),
        "closure_fmax_mhz": closure,
        "closure_fmax_interval_mhz": [closure, upper],
        "bisections": bisections,
        "trial_count": len(runner.trials),
        "trials": runner.trials,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivado", default="vivado")
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--candidate-id", action="append", default=[])
    parser.add_argument("--max-candidates", type=int, default=None)
    parser.add_argument("--trial-retries", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        manifest, digest = read_manifest()
        candidates = manifest["candidates"]
        if args.candidate_id:
            requested = set(args.candidate_id)
            candidates = [row for row in candidates
                          if row["candidate_id"] in requested]
            missing = requested - {row["candidate_id"] for row in candidates}
            if missing:
                raise RuntimeError(f"unknown candidate ids: {sorted(missing)}")
        if args.max_candidates is not None:
            candidates = candidates[:args.max_candidates]
        if not candidates:
            raise RuntimeError("no candidates selected")

        print(f"manifest_sha256={digest}")
        print(f"candidates={len(candidates)} dry_run={args.dry_run}")
        for index, candidate in enumerate(candidates, 1):
            print(f"[{index}/{len(candidates)}] {candidate['candidate_id']}")
            final_path = (Path(args.results) / candidate["candidate_id"]
                          / "closure_result.json")
            if final_path.is_file() and not args.dry_run:
                existing = json.loads(final_path.read_text(encoding="utf-8"))
                if existing.get("manifest_sha256") != digest:
                    raise RuntimeError(f"stale final result: {final_path}")
                print(f"  resume: {existing['status']}")
                continue
            runner = TrialRunner(
                args.vivado, candidate, digest, args.results,
                retries=args.trial_retries, dry_run=args.dry_run)
            result = close_candidate(candidate, digest, runner,
                                     dry_run=args.dry_run)
            if result is not None:
                atomic_json(final_path, result)
                print(f"  {result['status']}: "
                      f"{result.get('closure_fmax_mhz', 0.0):.6f} MHz")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
