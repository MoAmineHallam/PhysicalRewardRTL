#!/usr/bin/env python3
"""Run the frozen ten-candidate pilot with validated Vivado 2026.1."""

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
from timing_closure_gate_v7.stability_common import (  # noqa: E402
    VIVADO_ROOT, measurement_valid, raw_dependency_snapshot,
)

try:
    from .common import (
        BASELINE, V1, V7_ATTESTATION_SHA, atomic_json, read_json, sha256_file,
        verify_inputs, verify_package,
    )
except ImportError:
    from common import (
        BASELINE, V1, V7_ATTESTATION_SHA, atomic_json, read_json, sha256_file,
        verify_inputs, verify_package,
    )


DEFAULT_RESULTS = HERE / "results"
DEFAULT_SCRATCH = Path(r"C:\VGC7P001")
TCL = V1 / "closure_synth.tcl"
PART = "xc7z020clg400-1"
GUARD_READS = 3
STUDY_ID = "timing_closure_candidate_v7"


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


class TrialRunnerV7:
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

    def _load_ledger(self) -> list[dict]:
        if not self.ledger_path.is_file():
            return []
        rows = []
        for lineno, line in enumerate(
                self.ledger_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if (row.get("v1_manifest_sha256") != self.v1_digest
                    or row.get("candidate_package_sha256") != self.package_digest):
                raise RuntimeError(
                    f"stale ledger identity at {self.ledger_path}:{lineno}")
            rows.append(row)
        return rows

    def _append(self, row: dict) -> None:
        self.candidate_dir.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8", newline="\n") as out:
            out.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            out.flush()
            os.fsync(out.fileno())
        self.trials.append(row)

    def _matching(self, period: float, purpose: str) -> list[dict]:
        return [row for row in self.trials
                if row.get("purpose") == purpose
                and math.isclose(float(row["period_ns"]), period,
                                 rel_tol=0.0, abs_tol=5e-10)]

    def _next_sequence(self) -> int:
        return len(self.trials) + 1

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

    def run(self, period: float, purpose: str,
            force_fresh: bool = False) -> dict:
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
                    "valid_measurement": True, "closed": False,
                    "dry_run": True}

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
                raise RuntimeError(
                    f"refusing non-fresh trial/scratch: {trial_dir} / {scratch}")
            trial_dir.mkdir(parents=True)
            work_dir.mkdir(parents=True)
            temp_dir.mkdir(parents=True)
            result = trial_dir / "vivado_result.json"
            reports = trial_dir / "reports"
            stdout_path = trial_dir / "vivado.stdout.log"
            stderr_path = trial_dir / "vivado.stderr.log"
            before_ok, before, before_reason = dependency_guard(baseline)
            cmd = self.command(period, result, reports, temp_dir)
            completed = None
            if before_ok:
                with stdout_path.open("w", encoding="utf-8", errors="replace") as stdout, \
                        stderr_path.open("w", encoding="utf-8", errors="replace") as stderr:
                    completed = subprocess.run(
                        subprocess.list2cmdline(cmd), cwd=work_dir,
                        stdout=stdout, stderr=stderr, shell=True, check=False)
            else:
                stdout_path.write_text(
                    "launch blocked by dependency guard\n", encoding="utf-8")
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
                "study_id": STUDY_ID,
                "v1_manifest_sha256": self.v1_digest,
                "candidate_package_sha256": self.package_digest,
                "v7_stability_attestation_sha256": V7_ATTESTATION_SHA,
                "vivado_version": "2026.1",
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
                "before_dependency_guard": {
                    "ok": before_ok, "reason": before_reason,
                    "aggregate_sha256_raw": before.get("aggregate_sha256_raw")},
                "after_dependency_guard": {
                    "ok": after_ok, "reason": after_reason,
                    "aggregate_sha256_raw": after.get("aggregate_sha256_raw")},
                "vivado": parsed,
                "stdout_sha256_raw": sha256_file(stdout_path),
                "stderr_sha256_raw": sha256_file(stderr_path),
                "result_sha256_raw": sha256_file(result)
                    if result.is_file() else None,
            }
            atomic_json(trial_dir / "trial_record.json", row)
            self._append(row)
            last = row
            if valid:
                return row
        return last


def bind_result(result: dict, v1_digest: str,
                package_digest: str) -> dict:
    value = dict(result)
    observed_v1 = value.pop("manifest_sha256", None)
    if observed_v1 != v1_digest:
        raise RuntimeError("V1 close_candidate returned an unexpected identity")
    value.update({
        "study_id": STUDY_ID,
        "v1_manifest_sha256": v1_digest,
        "candidate_package_sha256": package_digest,
        "v7_stability_attestation_sha256": V7_ATTESTATION_SHA,
        "vivado_version": "2026.1",
    })
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivado", default=str(
        VIVADO_ROOT / "bin" / "vivado.bat"))
    parser.add_argument("--results", default=str(DEFAULT_RESULTS))
    parser.add_argument("--scratch-root", default=str(DEFAULT_SCRATCH))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        manifest, v1_digest = verify_inputs()
        package_digest = verify_package()
        results = Path(args.results)
        scratch = Path(args.scratch_root)
        print(f"v1_manifest_sha256={v1_digest}")
        print(f"candidate_package_sha256={package_digest}")
        print(f"candidates={len(manifest['candidates'])} dry_run={args.dry_run}")
        for index, candidate in enumerate(manifest["candidates"], 1):
            print(f"[{index}/10] {candidate['candidate_id']}", flush=True)
            final_path = results / candidate["candidate_id"] / "closure_result.json"
            if final_path.exists() and not args.dry_run:
                raise RuntimeError(f"refusing existing final result: {final_path}")
            runner = TrialRunnerV7(
                Path(args.vivado), candidate, index, v1_digest,
                package_digest, results, scratch, retries=1,
                dry_run=args.dry_run)
            result = v1run.close_candidate(
                candidate, v1_digest, runner, dry_run=args.dry_run)
            if result is not None:
                bound = bind_result(result, v1_digest, package_digest)
                atomic_json(final_path, bound)
                print(f"  {bound['status']}: "
                      f"{bound.get('closure_fmax_mhz', 0.0):.6f} MHz",
                      flush=True)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
