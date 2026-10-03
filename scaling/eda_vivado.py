#!/usr/bin/env python3
"""Parallel Vivado implementation with the frozen primary flow, and its calibration.

    python scaling/eda_vivado.py run --dir <circuits> --out <dir>/ppa.jsonl --jobs 24
    python scaling/eda_vivado.py calibrate --ref-dir gate0/vivado --out phase0/vivado_calib

``run`` implements every ``<module>.sv``/``.v`` in a directory with the previous
project's ``run_ppa.run_one`` (``ppa_synth.tcl``: Vivado 2023.1, ``xc7z020clg400-1``,
out-of-context synthesis, place and route, 5.0 ns request), so each record has
exactly the fields the laptop flow writes, plus ``host`` and ``wall_s``.  Jobs run
in parallel, each Vivado in its own working directory; finished modules are
skipped on restart.

``calibrate`` re-implements a fixed, hash-ordered sample of circuits that the
laptop already implemented (Gate 0) and compares the two sets of records against
the rule written in ``research/fpga2/PHASE0_STATUS.md`` before the first run.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as _dt
import glob
import hashlib
import json
import os
import socket
import statistics
import sys
import tempfile
import time
from typing import Dict, List, Optional, Sequence

MAS = "/zeng_gk/Amine/mas"
DEFAULT_VIVADO = f"{MAS}/Xilinx/Vivado/2023.1/bin/vivado"
DEFAULT_FPGA_ROOT = f"{MAS}/fpga"
# Vivado's rdiArgs.sh forces LC_ALL=en_US.UTF-8, which the containers lack; the locale
# is compiled once onto the share and found through LOCPATH (no Vivado file is edited).
DEFAULT_LOCPATH = f"{MAS}/locale"
CALIB_N = 20

# Calibration rule (frozen before the first server run; see PHASE0_STATUS.md).
RESOURCE_KEYS = ("lut", "ff", "dsp", "bram")
FMAX_REL_TOL = 0.01      # a circuit "agrees" if |dFmax| <= 1% of the laptop value
MIN_RESOURCE_MATCH = 19  # of 20: identical LUT/FF/DSP/BRAM counts
MIN_FMAX_MATCH = 18      # of 20: within FMAX_REL_TOL
MAX_FMAX_REL = 0.03      # and no circuit off by more than 3%

_run_one = None
# Text in a failed job's output that means Vivado itself did not run.
INFRA_MARKERS = ("terminate called", "setlocale", "command not found", "No such file or directory")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_records(path: str) -> Dict[str, dict]:
    """Last record per module; unreadable lines are ignored, as in run_ppa.load_done."""
    records: Dict[str, dict] = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    rec = json.loads(line)
                    records[rec["module"]] = rec
                except (ValueError, KeyError):
                    pass
    return records


def list_circuits(directory: str) -> List[str]:
    return sorted(glob.glob(os.path.join(directory, "*.sv")) + glob.glob(os.path.join(directory, "*.v")))


def vivado_env(locpath: Optional[str]) -> dict:
    env = dict(os.environ)
    if locpath and os.path.isdir(os.path.join(locpath, "en_US.UTF-8")):
        env["LOCPATH"] = locpath
    return env


def preflight(vivado: str, locpath: Optional[str]) -> str:
    """Vivado must start and report 2023.1 before any job, so an environment failure can
    never be recorded as a circuit that failed to synthesise."""
    import subprocess
    try:
        cp = subprocess.run([vivado, "-version"], capture_output=True, text=True,
                            env=vivado_env(locpath), timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"Vivado preflight failed: {exc}")
    first = next((l for l in cp.stdout.splitlines() if l.lower().startswith("vivado v")), "")
    if cp.returncode != 0 or not first.lower().startswith("vivado v2023.1"):
        raise SystemExit("Vivado preflight failed (nothing was run or recorded):\n"
                         + (cp.stdout + cp.stderr)[-1500:])
    return first.strip()


def _init_worker(fpga_root: str, locpath: Optional[str] = None) -> None:
    global _run_one
    if locpath and os.path.isdir(os.path.join(locpath, "en_US.UTF-8")):
        os.environ["LOCPATH"] = locpath
    sys.path.insert(0, fpga_root)
    import run_ppa  # the previous project's frozen flow
    _run_one = run_ppa.run_one
    os.chdir(tempfile.mkdtemp(prefix="vivado_job_"))  # Vivado writes .Xil/ into the cwd


def _job(vivado: str, vfile: str, clk: str, period: float) -> dict:
    top = os.path.splitext(os.path.basename(vfile))[0]
    start = time.time()
    rec = _run_one(vivado, vfile, top, clk, period)
    rec["module"] = top
    rec["host"] = socket.gethostname()
    rec["wall_s"] = round(time.time() - start, 1)
    return rec


def run_parallel(files: Sequence[str], out: str, vivado: str, fpga_root: str,
                 jobs: int, clk: str = "clk", period: float = 5.0,
                 locpath: Optional[str] = DEFAULT_LOCPATH) -> dict:
    version = preflight(vivado, locpath)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    done = set(load_records(out))
    todo = [f for f in files if os.path.splitext(os.path.basename(f))[0] not in done]
    meta = {
        "started": _dt.datetime.now().isoformat(timespec="seconds"),
        "host": socket.gethostname(), "jobs": jobs, "vivado": vivado, "period_ns": period,
        "vivado_version": version, "locpath": vivado_env(locpath).get("LOCPATH"),
        "run_ppa_sha256": sha256_file(os.path.join(fpga_root, "run_ppa.py")),
        "ppa_synth_tcl_sha256": sha256_file(os.path.join(fpga_root, "ppa_synth.tcl")),
        "n_files": len(files), "n_skipped": len(files) - len(todo),
    }
    n_ok = n_fail = 0
    t0 = time.time()
    with open(out, "a", encoding="utf-8") as fout, cf.ProcessPoolExecutor(
            max_workers=jobs, initializer=_init_worker, initargs=(fpga_root, locpath)) as pool:
        futures = {pool.submit(_job, vivado, os.path.abspath(f), clk, period): f for f in todo}
        for i, fut in enumerate(cf.as_completed(futures), 1):
            rec = fut.result()
            if not rec.get("compiled") and any(m in rec.get("error", "") for m in INFRA_MARKERS):
                raise SystemExit(f"{rec['module']}: Vivado did not run ({rec['error'][-200:]!r}); "
                                 "nothing recorded for it - fix the environment and rerun")
            fout.write(json.dumps(rec) + "\n")
            fout.flush()
            if rec.get("compiled"):
                n_ok += 1
                tag = f"fmax={rec.get('fmax_mhz', 0):.1f}MHz lut={rec.get('lut', 0)} ({rec['wall_s']}s)"
            else:
                n_fail += 1
                tag = "SYNTH FAIL"
            print(f"[{i}/{len(todo)}] {rec['module']}: {tag}", flush=True)
    elapsed = time.time() - t0
    meta.update({"finished": _dt.datetime.now().isoformat(timespec="seconds"),
                 "n_run": len(todo), "n_ok": n_ok, "n_fail": n_fail,
                 "elapsed_s": round(elapsed, 1),
                 "circuits_per_hour": round(3600 * len(todo) / elapsed, 1) if todo and elapsed else None})
    with open(out + ".meta.jsonl", "a", encoding="utf-8") as handle:
        handle.write(json.dumps(meta) + "\n")
    return meta


# ------------------------------------------------------------------ calibration

def calibration_sample(ref: Dict[str, dict], available: Sequence[str], n: int = CALIB_N) -> List[str]:
    """First n modules by sha256(module) among those with a laptop record and a file."""
    pool = [m for m in available if m in ref]
    return sorted(pool, key=lambda m: hashlib.sha256(m.encode()).hexdigest())[:n]


def compare(ref: Dict[str, dict], new: Dict[str, dict], modules: Sequence[str]) -> dict:
    rows, compiled_agree, resource_match, fmax_match = [], 0, 0, 0
    rel_errors: List[float] = []
    for m in modules:
        a, b = ref[m], new.get(m)
        row = {"module": m, "laptop": a, "server": b}
        if b is None:
            row["status"] = "missing"
            rows.append(row)
            continue
        same_compiled = bool(a.get("compiled")) == bool(b.get("compiled"))
        compiled_agree += same_compiled
        if a.get("compiled") and b.get("compiled"):
            res = all(int(a.get(k, 0)) == int(b.get(k, 0)) for k in RESOURCE_KEYS)
            fa, fb = float(a.get("fmax_mhz", 0)), float(b.get("fmax_mhz", 0))
            rel = abs(fb - fa) / fa if fa else (0.0 if fb == 0 else float("inf"))
            rel_errors.append(rel)
            resource_match += res
            fmax_match += rel <= FMAX_REL_TOL
            row.update({"resources_equal": res, "fmax_rel_diff": rel})
        elif same_compiled:  # both failed: counts as agreement everywhere
            resource_match += 1
            fmax_match += 1
            rel_errors.append(0.0)
        rows.append(row)
    n = len(modules)
    max_rel = max(rel_errors) if rel_errors else None
    passed = (n == CALIB_N and compiled_agree == n and resource_match >= MIN_RESOURCE_MATCH
              and fmax_match >= MIN_FMAX_MATCH and max_rel is not None and max_rel <= MAX_FMAX_REL)
    return {
        "n": n, "compiled_agree": compiled_agree, "resource_match": resource_match,
        "fmax_within_1pct": fmax_match,
        "median_fmax_rel_diff": statistics.median(rel_errors) if rel_errors else None,
        "max_fmax_rel_diff": max_rel, "pass": passed,
        "rule": {"n": CALIB_N, "compiled_agree": "all", "resource_match_min": MIN_RESOURCE_MATCH,
                 "fmax_rel_tol": FMAX_REL_TOL, "fmax_match_min": MIN_FMAX_MATCH,
                 "max_fmax_rel": MAX_FMAX_REL},
        "rows": rows,
    }


def cmd_run(args: argparse.Namespace) -> None:
    files = list_circuits(args.dir) if args.dir else []
    files += args.files or []
    if not files:
        raise SystemExit("no input files (use --dir or --files)")
    meta = run_parallel(files, args.out, args.vivado, args.fpga_root, args.jobs, args.clk, args.period,
                        args.locpath)
    print(json.dumps({k: v for k, v in meta.items() if not k.endswith("sha256")}, indent=1))


def cmd_calibrate(args: argparse.Namespace) -> None:
    ref = load_records(os.path.join(args.ref_dir, "ppa.jsonl"))
    available = [os.path.splitext(os.path.basename(f))[0] for f in list_circuits(args.ref_dir)]
    sample = calibration_sample(ref, available, args.n)
    if len(sample) < args.n:
        raise SystemExit(f"only {len(sample)} circuits with laptop records in {args.ref_dir}")
    os.makedirs(args.out, exist_ok=True)
    files = [os.path.join(args.ref_dir, m + ".sv") for m in sample]
    files = [f if os.path.isfile(f) else f[:-3] + ".v" for f in files]
    out = os.path.join(args.out, "ppa.jsonl")
    meta = run_parallel(files, out, args.vivado, args.fpga_root, args.jobs, locpath=args.locpath)
    result = compare(ref, load_records(out), sample)
    result["meta"] = meta
    with open(os.path.join(args.out, "calibration.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=1)
        handle.write("\n")
    for row in result["rows"]:
        a, b = row["laptop"], row["server"] or {}
        print(f"{row['module']:<44} laptop {a.get('fmax_mhz', 0):8.2f}  server {b.get('fmax_mhz', 0):8.2f}"
              f"  res {'=' if row.get('resources_equal', True) else 'DIFF'}")
    summary = {k: result[k] for k in ("n", "compiled_agree", "resource_match", "fmax_within_1pct",
                                      "median_fmax_rel_diff", "max_fmax_rel_diff", "pass")}
    summary["circuits_per_hour"] = meta.get("circuits_per_hour")
    print(json.dumps(summary, indent=1))


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "calibrate"):
        p = sub.add_parser(name)
        p.add_argument("--vivado", default=DEFAULT_VIVADO)
        p.add_argument("--fpga-root", default=DEFAULT_FPGA_ROOT,
                       help="previous-project checkout providing run_ppa.py and ppa_synth.tcl")
        p.add_argument("--jobs", type=int, default=8)
        p.add_argument("--locpath", default=DEFAULT_LOCPATH,
                       help="directory holding a compiled en_US.UTF-8 locale (used if present)")
    r = sub.choices["run"]
    r.add_argument("--dir")
    r.add_argument("--files", nargs="*")
    r.add_argument("--out", required=True)
    r.add_argument("--clk", default="clk")
    r.add_argument("--period", type=float, default=5.0)
    c = sub.choices["calibrate"]
    c.add_argument("--ref-dir", required=True, help="directory with laptop ppa.jsonl and the .sv files")
    c.add_argument("--out", required=True)
    c.add_argument("--n", type=int, default=CALIB_N)
    args = ap.parse_args(argv)
    {"run": cmd_run, "calibrate": cmd_calibrate}[args.cmd](args)


if __name__ == "__main__":
    main()
