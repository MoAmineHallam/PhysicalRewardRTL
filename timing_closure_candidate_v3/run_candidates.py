#!/usr/bin/env python3
"""Run the frozen ten-candidate pilot with the validated V3 infrastructure."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from timing_closure_gate_v1 import run_closure as v1run  # noqa: E402
from timing_closure_gate_v3.stability_common import (  # noqa: E402
    VIVADO_ROOT, measurement_valid, raw_dependency_snapshot)

try:
    from .common import (BASELINE, V1, atomic_json, read_json, sha256_file,
                         verify_inputs, verify_package)
except ImportError:
    from common import (BASELINE, V1, atomic_json, read_json, sha256_file,
                        verify_inputs, verify_package)


DEFAULT_RESULTS = HERE / "results"
DEFAULT_SCRATCH = Path(r"C:\VGC3P001")
TCL = V1 / "closure_synth.tcl"
PART = "xc7z020clg400-1"
GUARD_READS = 3


def dependency_guard(baseline: dict) -> tuple[bool, dict, str | None]:
    try:
        actual = raw_dependency_snapshot(VIVADO_ROOT)
        for _ in range(1, GUARD_READS):
            if raw_dependency_snapshot(VIVADO_ROOT) != actual:
                return False, actual, "dependency_guard_inconsistent_reads"
    except Exception as exc:
        return False, {"error": str(exc)}, "dependency_guard_read_failure"
    comparable = {key: baseline[key] for key in actual}
    if actual != comparable:
        return False, actual, "dependency_guard_changed"
    return True, actual, None


def latest_monotonic_contradictions(trials: list[dict]) -> list[tuple[float, float]]:
    latest: dict[float, dict] = {}
    for row in trials:
        if row.get("valid_measurement"):
            latest[float(row["period_ns"])] = row
    passed = [period for period, row in latest.items() if row["closed"]]
    failed = [period for period, row in latest.items() if not row["closed"]]
    return sorted((p_pass, p_fail) for p_pass in passed for p_fail in failed
                  if p_pass + 1e-9 < p_fail)


class TrialRunner:
    def __init__(self, vivado: Path, candidate: dict, candidate_number: int,
                 v1_digest: str, package_digest: str, results: Path,
                 scratch: Path, retries: int = 1, dry_run: bool = False):
        self.vivado = Path(vivado)
        self.candidate = candidate
        self.candidate_number = candidate_number
        self.v1_digest = v1_digest
        self.package_digest = package_digest
        self.candidate_dir = Path(results) / candidate["candidate_id"]
        self.scratch_dir = Path(scratch) / f"c{candidate_number:02d}"
        self.ledger_path = self.candidate_dir / "trials.jsonl"
        self.retries = retries
        self.dry_run = dry_run
        self.trials = self._load_ledger()
        if not dry_run:
            self._recover_completed_records()

    def _load_ledger(self) -> list[dict]:
        if not self.ledger_path.is_file():
            return []
        rows = []
        for lineno, line in enumerate(
                self.ledger_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("v1_manifest_sha256") != self.v1_digest:
                raise RuntimeError(f"stale V1 identity at {self.ledger_path}:{lineno}")
            if row.get("candidate_package_sha256") != self.package_digest:
                raise RuntimeError(f"stale package identity at {self.ledger_path}:{lineno}")
            rows.append(row)
        return rows

    def _append(self, row: dict) -> None:
        self.candidate_dir.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8", newline="\n") as out:
            out.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            out.flush()
            os.fsync(out.fileno())
        self.trials.append(row)

    def _recover_completed_records(self) -> None:
        known = {row.get("trial_dir") for row in self.trials}
        if not self.candidate_dir.is_dir():
            return
        for trial_dir in sorted(self.candidate_dir.glob("trial_*")):
            relative = trial_dir.resolve().relative_to(ROOT).as_posix()
            if relative in known:
                continue
            record_path = trial_dir / "trial_record.json"
            launch_path = trial_dir / "launch_record.json"
            if record_path.is_file():
                row = read_json(record_path)
                if row.get("trial_dir") != relative:
                    raise RuntimeError(f"orphan record identity mismatch: {record_path}")
                self._append(row)
            elif launch_path.is_file():
                launch = read_json(launch_path)
                row = self._interrupted_row(trial_dir, launch)
                atomic_json(record_path, row, replace=False)
                self._append(row)
            else:
                raise RuntimeError(f"unrecognized orphan trial directory: {trial_dir}")

    def _interrupted_row(self, trial_dir: Path, launch: dict) -> dict:
        stdout = trial_dir / "vivado.stdout.log"
        stderr = trial_dir / "vivado.stderr.log"
        result = trial_dir / "vivado_result.json"
        return {
            "schema_version": 1,
            "study_id": "timing_closure_candidate_v3",
            "v1_manifest_sha256": self.v1_digest,
            "candidate_package_sha256": self.package_digest,
            "candidate_id": self.candidate["candidate_id"],
            "period_ns": launch["period_ns"],
            "purpose": launch["purpose"],
            "attempt": launch["attempt"],
            "trial_dir": trial_dir.resolve().relative_to(ROOT).as_posix(),
            "returncode": None,
            "parse_error": "interrupted_before_trial_record_publication",
            "valid_measurement": False,
            "closed": False,
            "classification": "interrupted_process",
            "before_dependency_guard": launch.get("before_dependency_guard"),
            "after_dependency_guard": None,
            "vivado": {},
            "stdout_sha256_raw": sha256_file(stdout) if stdout.is_file() else None,
            "stderr_sha256_raw": sha256_file(stderr) if stderr.is_file() else None,
            "result_sha256_raw": sha256_file(result) if result.is_file() else None,
        }

    def _matching(self, period: float, purpose: str) -> list[dict]:
        return [row for row in self.trials
                if row.get("purpose") == purpose
                and math.isclose(float(row["period_ns"]), period,
                                 rel_tol=0.0, abs_tol=5e-10)]

    def _next_sequence(self) -> int:
        maximum = 0
        if self.candidate_dir.is_dir():
            for path in self.candidate_dir.glob("trial_*" ):
                try:
                    maximum = max(maximum, int(path.name.split("_", 2)[1]))
                except (IndexError, ValueError):
                    raise RuntimeError(f"unrecognized trial path: {path}")
        return maximum + 1

    def command(self, period: float, result: Path, reports: Path,
                temp_dir: Path) -> list[str]:
        source = ROOT / self.candidate["materialized_path"]
        return [
            str(self.vivado), "-mode", "batch", "-nojournal", "-nolog",
            "-notrace", "-tempDir", str(temp_dir), "-source", str(TCL),
            "-tclargs", str(source), self.candidate["module"],
            self.candidate["clock_port"], f"{period:.12g}", str(result),
            str(reports), PART,
        ]

    def run(self, period: float, purpose: str, force_fresh: bool = False) -> dict:
        period = float(period)
        matching = self._matching(period, purpose)
        if not force_fresh:
            valid = [row for row in matching if row.get("valid_measurement")]
            if valid:
                return valid[-1]
        start_attempt = len(matching)
        if start_attempt > self.retries:
            return matching[-1]
        if self.dry_run:
            sequence = self._next_sequence()
            scratch = self.scratch_dir / f"t{sequence:03d}"
            cmd = self.command(period, Path("RESULT.json"), Path("REPORTS"),
                               scratch / "t")
            print(subprocess.list2cmdline(cmd))
            return {"period_ns": period, "purpose": purpose,
                    "valid_measurement": True, "closed": False, "dry_run": True}

        baseline = read_json(BASELINE)
        last = None
        for attempt in range(start_attempt, self.retries + 1):
            sequence = self._next_sequence()
            token = v1run.period_token(period)
            trial_dir = self.candidate_dir / (
                f"trial_{sequence:03d}_{purpose}_p{token}_a{attempt}")
            scratch = self.scratch_dir / f"t{sequence:03d}"
            work_dir, temp_dir = scratch / "w", scratch / "t"
            if trial_dir.exists() or scratch.exists():
                raise RuntimeError(f"refusing non-fresh trial/scratch: {trial_dir} / {scratch}")
            trial_dir.mkdir(parents=True)
            work_dir.mkdir(parents=True)
            temp_dir.mkdir(parents=True)
            result = trial_dir / "vivado_result.json"
            reports = trial_dir / "reports"
            stdout_path = trial_dir / "vivado.stdout.log"
            stderr_path = trial_dir / "vivado.stderr.log"
            before_ok, before, before_reason = dependency_guard(baseline)
            cmd = self.command(period, result, reports, temp_dir)
            launch = {
                "schema_version": 1,
                "study_id": "timing_closure_candidate_v3",
                "v1_manifest_sha256": self.v1_digest,
                "candidate_package_sha256": self.package_digest,
                "candidate_id": self.candidate["candidate_id"],
                "period_ns": period,
                "purpose": purpose,
                "attempt": attempt,
                "command": cmd,
                "before_dependency_guard": {"ok": before_ok,
                                              "reason": before_reason,
                                              "snapshot": before},
                "scratch_work_dir": str(work_dir),
                "scratch_temp_dir": str(temp_dir),
            }
            atomic_json(trial_dir / "launch_record.json", launch, replace=False)
            completed = None
            if before_ok:
                with stdout_path.open("w", encoding="utf-8", errors="replace") as stdout, \
                        stderr_path.open("w", encoding="utf-8", errors="replace") as stderr:
                    completed = subprocess.run(
                        subprocess.list2cmdline(cmd), cwd=work_dir, stdout=stdout,
                        stderr=stderr, shell=True, check=False)
            else:
                stdout_path.write_text("launch blocked by dependency guard\n",
                                       encoding="utf-8")
                stderr_path.write_text("", encoding="utf-8")
            after_ok, after, after_reason = dependency_guard(baseline)
            parsed, parse_error = {}, None
            try:
                parsed = read_json(result)
            except Exception as exc:
                parse_error = str(exc)
            valid = (before_ok and after_ok and completed is not None
                     and completed.returncode == 0 and measurement_valid(parsed))
            if not before_ok:
                classification = before_reason
            elif not after_ok:
                classification = after_reason
            elif valid:
                classification = "VALID_CANDIDATE_MEASUREMENT"
            else:
                classification = "candidate_vivado_or_parse_failure"
            row = {
                "schema_version": 1,
                "study_id": "timing_closure_candidate_v3",
                "v1_manifest_sha256": self.v1_digest,
                "candidate_package_sha256": self.package_digest,
                "candidate_id": self.candidate["candidate_id"],
                "period_ns": period,
                "purpose": purpose,
                "attempt": attempt,
                "trial_dir": trial_dir.resolve().relative_to(ROOT).as_posix(),
                "returncode": None if completed is None else completed.returncode,
                "parse_error": parse_error,
                "valid_measurement": valid,
                "closed": bool(valid and int(parsed.get("closed", 0)) == 1),
                "classification": classification,
                "before_dependency_guard": {"ok": before_ok,
                                              "reason": before_reason,
                                              "aggregate_sha256_raw": before.get(
                                                  "aggregate_sha256_raw")},
                "after_dependency_guard": {"ok": after_ok,
                                             "reason": after_reason,
                                             "aggregate_sha256_raw": after.get(
                                                 "aggregate_sha256_raw")},
                "vivado": parsed,
                "stdout_sha256_raw": sha256_file(stdout_path),
                "stderr_sha256_raw": sha256_file(stderr_path),
                "result_sha256_raw": sha256_file(result) if result.is_file() else None,
            }
            atomic_json(trial_dir / "trial_record.json", row, replace=False)
            self._append(row)
            last = row
            if valid:
                return row
        return last


def result_identity(candidate: dict, v1_digest: str,
                    package_digest: str) -> dict:
    return {
        "schema_version": 1,
        "study_id": "timing_closure_candidate_v3",
        "scope": "pilot_10",
        "v1_manifest_sha256": v1_digest,
        "candidate_package_sha256": package_digest,
        "candidate_id": candidate["candidate_id"],
        "family": candidate["family"],
        "design": candidate["design"],
        "arm": candidate["arm"],
        "module": candidate["module"],
        "old_fmax_mhz": candidate["old_fmax_mhz"],
    }


def fail_result(candidate: dict, v1_digest: str, package_digest: str,
                trials: list[dict], reason: str) -> dict:
    value = result_identity(candidate, v1_digest, package_digest)
    value.update({"status": "FAILED", "failure_reason": reason,
                  "closure_fmax_mhz": 0.0, "trial_count": len(trials),
                  "trials": trials})
    return value


def close_candidate(candidate: dict, v1_digest: str, package_digest: str,
                    runner: TrialRunner, dry_run: bool = False) -> dict | None:
    delay = float(candidate["old_proxy_delay_ns"])
    floor, ceiling = 1.0, 200.0
    tight, loose = v1run.initial_periods(delay, floor, ceiling)
    if dry_run:
        runner.run(tight, "initial_tight")
        runner.run(loose, "initial_loose")
        return None

    tight_row = runner.run(tight, "search")
    loose_row = runner.run(loose, "search")
    if not tight_row.get("valid_measurement") or not loose_row.get("valid_measurement"):
        return fail_result(candidate, v1_digest, package_digest, runner.trials,
                           "permanent_invalid_initial_measurement")

    expansions = 0
    while tight_row["closed"] and expansions < 4 and tight > floor:
        tight = max(floor, tight / 1.5)
        tight_row = runner.run(tight, "search")
        if not tight_row.get("valid_measurement"):
            return fail_result(candidate, v1_digest, package_digest, runner.trials,
                               "permanent_invalid_tight_expansion")
        expansions += 1
    if tight_row["closed"]:
        return fail_result(candidate, v1_digest, package_digest, runner.trials,
                           "no_failing_period_within_preregistered_floor")

    expansions = 0
    while not loose_row["closed"] and expansions < 4 and loose < ceiling:
        loose = min(ceiling, loose * 1.5)
        loose_row = runner.run(loose, "search")
        if not loose_row.get("valid_measurement"):
            return fail_result(candidate, v1_digest, package_digest, runner.trials,
                               "permanent_invalid_loose_expansion")
        expansions += 1
    if not loose_row["closed"]:
        return fail_result(candidate, v1_digest, package_digest, runner.trials,
                           "no_passing_period_within_preregistered_ceiling")

    bisections = 0
    while v1run.relative_bracket_width(tight, loose) > 0.01 and bisections < 10:
        midpoint = 0.5 * (tight + loose)
        row = runner.run(midpoint, "search")
        if not row.get("valid_measurement"):
            return fail_result(candidate, v1_digest, package_digest, runner.trials,
                               "permanent_invalid_bisection_measurement")
        if row["closed"]:
            loose, loose_row = midpoint, row
        else:
            tight, tight_row = midpoint, row
        bisections += 1
    if v1run.relative_bracket_width(tight, loose) > 0.01:
        return fail_result(candidate, v1_digest, package_digest, runner.trials,
                           "bisection_tolerance_not_reached")

    contradictions = latest_monotonic_contradictions(runner.trials)
    if contradictions:
        periods = sorted({period for pair in contradictions for period in pair})
        for period in periods:
            latest = [row for row in runner.trials
                      if row.get("valid_measurement")
                      and math.isclose(float(row["period_ns"]), period,
                                       rel_tol=0.0, abs_tol=5e-10)][-1]
            purpose = "monotonic_recheck_pass" if latest["closed"] \
                else "monotonic_recheck_fail"
            row = runner.run(period, purpose, force_fresh=True)
            if not row.get("valid_measurement"):
                return fail_result(candidate, v1_digest, package_digest,
                                   runner.trials,
                                   "invalid_nonmonotonic_recheck")
        contradictions = latest_monotonic_contradictions(runner.trials)
        if contradictions:
            return fail_result(candidate, v1_digest, package_digest, runner.trials,
                               f"persistent_nonmonotonic_search:{contradictions}")

    confirm_fail = runner.run(tight, "confirm_fail", force_fresh=True)
    confirm_pass = runner.run(loose, "confirm_pass", force_fresh=True)
    if (not confirm_fail.get("valid_measurement")
            or not confirm_pass.get("valid_measurement")):
        return fail_result(candidate, v1_digest, package_digest, runner.trials,
                           "permanent_invalid_boundary_confirmation")
    if confirm_fail["closed"] or not confirm_pass["closed"]:
        return fail_result(candidate, v1_digest, package_digest, runner.trials,
                           "nondeterministic_boundary_confirmation")

    value = result_identity(candidate, v1_digest, package_digest)
    closure = 1000.0 / loose
    value.update({
        "status": "COMPLETE",
        "failure_reason": None,
        "tight_failing_period_ns": tight,
        "loose_passing_period_ns": loose,
        "relative_bracket_width": v1run.relative_bracket_width(tight, loose),
        "closure_fmax_mhz": closure,
        "closure_fmax_interval_mhz": [closure, 1000.0 / tight],
        "bisections": bisections,
        "trial_count": len(runner.trials),
        "trials": runner.trials,
    })
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivado", default=str(VIVADO_ROOT / "bin" / "vivado.bat"))
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--scratch-root", default=str(DEFAULT_SCRATCH))
    parser.add_argument("--candidate-id", action="append", default=[])
    parser.add_argument("--max-candidates", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        manifest, v1_digest = verify_inputs()
        package_digest = verify_package()
        candidates = list(manifest["candidates"])
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
        original_order = {row["candidate_id"]: index
                          for index, row in enumerate(manifest["candidates"], 1)}
        print(f"v1_manifest_sha256={v1_digest}")
        print(f"candidate_package_sha256={package_digest}")
        print(f"candidates={len(candidates)} dry_run={args.dry_run}")
        for position, candidate in enumerate(candidates, 1):
            print(f"[{position}/{len(candidates)}] {candidate['candidate_id']}",
                  flush=True)
            final_path = (Path(args.results) / candidate["candidate_id"]
                          / "closure_result.json")
            if final_path.is_file() and not args.dry_run:
                existing = read_json(final_path)
                if (existing.get("v1_manifest_sha256") != v1_digest
                        or existing.get("candidate_package_sha256") != package_digest):
                    raise RuntimeError(f"stale final result: {final_path}")
                print(f"  resume: {existing['status']}", flush=True)
                continue
            runner = TrialRunner(
                Path(args.vivado), candidate,
                original_order[candidate["candidate_id"]], v1_digest,
                package_digest, Path(args.results), Path(args.scratch_root),
                retries=1, dry_run=args.dry_run)
            result = close_candidate(candidate, v1_digest, package_digest,
                                     runner, dry_run=args.dry_run)
            if result is not None:
                atomic_json(final_path, result, replace=False)
                print(f"  {result['status']}: "
                      f"{result.get('closure_fmax_mhz', 0.0):.6f} MHz",
                      flush=True)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
