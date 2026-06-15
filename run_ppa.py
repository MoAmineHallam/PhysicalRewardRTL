#!/usr/bin/env python3
"""
run_ppa.py  -  Batch-run ppa_synth.tcl over many RTL files (laptop, Vivado).

Two purposes:
  1. Lever 3 data: per-candidate post-implementation timing/area/power -- the
     "physical quality" signal a functional simulator cannot produce. Pairs
     with each candidate's functional reward to show functionally-equivalent
     designs differ physically.
  2. Synthesis pre-screen: any file that reports compiled:0 won't synthesize
     in Vivado and would otherwise break a 64-candidate batch build. Feed the
     failing module list back to gen_candidate_bitstream --exclude.

Each .v file's top module is taken to be its filename stem (the candidate
files written by gen_candidate_bitstream are named <module>.v with the module
renamed to match).

Usage (laptop, in the repo, Vivado on PATH):
    python run_ppa.py --dir rtl/cand_batches/cand --out rtl/cand_batches/ppa.jsonl
    python run_ppa.py --dir rtl/cand_batches/cand --period 5.0   # 200 MHz target
    python run_ppa.py --files a.v b.v --clk clk

Resumable: modules already in --out are skipped. Emits a failing-module list
to <out>.fails so it can be passed to gen_candidate_bitstream --exclude.
"""

import os
import re
import sys
import json
import glob
import argparse
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TCL = os.path.join(ROOT, "ppa_synth.tcl")


def load_done(out_path):
    done = set()
    if os.path.exists(out_path):
        for line in open(out_path):
            try:
                done.add(json.loads(line)["module"])
            except (ValueError, KeyError):
                pass
    return done


def run_one(vivado, vfile, top, clk, period):
    """Run ppa_synth.tcl on one file; return the parsed PPA dict."""
    with tempfile.TemporaryDirectory() as wd:
        outj = os.path.join(wd, "ppa.json")
        cmd = [vivado, "-mode", "batch", "-nojournal", "-nolog",
               "-source", TCL, "-tclargs", vfile, top, clk,
               str(period), outj]
        if os.name == "nt":
            # vivado is a .bat on Windows -> needs the shell; quote args w/ spaces
            cmd = " ".join(f'"{c}"' if " " in c else c for c in cmd)
            cp = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        else:
            cp = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(outj):
            try:
                return json.load(open(outj))
            except ValueError:
                pass
        # synth crashed before emitting -- record a failure with a hint
        tail = (cp.stdout or "")[-200:].replace("\n", " ")
        return {"compiled": 0, "error": tail}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=None,
                    help="directory of <module>.v files")
    ap.add_argument("--files", nargs="*", default=None)
    ap.add_argument("--out", default="ppa.jsonl")
    ap.add_argument("--vivado", default="vivado")
    ap.add_argument("--clk", default="clk", help="clock port name")
    ap.add_argument("--period", type=float, default=5.0,
                    help="target clock period ns (5.0 = 200 MHz)")
    args = ap.parse_args()

    files = []
    if args.dir:
        files += sorted(glob.glob(os.path.join(args.dir, "*.sv"))
                        + glob.glob(os.path.join(args.dir, "*.v")))
    if args.files:
        files += args.files
    if not files:
        print("no input files (use --dir or --files)", file=sys.stderr)
        sys.exit(1)

    done = load_done(args.out)
    n_ok = n_fail = 0
    with open(args.out, "a") as fout:
        for i, vfile in enumerate(files):
            top = os.path.splitext(os.path.basename(vfile))[0]
            if top in done:
                continue
            rec = run_one(args.vivado, vfile, top, args.clk, args.period)
            rec["module"] = top
            fout.write(json.dumps(rec) + "\n")
            fout.flush()
            if rec.get("compiled"):
                n_ok += 1
                tag = (f"fmax={rec.get('fmax_mhz', 0):.0f}MHz "
                       f"lut={rec.get('lut', 0)} ff={rec.get('ff', 0)} "
                       f"pw={rec.get('power_w', 0)}W")
            else:
                n_fail += 1
                tag = "SYNTH FAIL"
            print(f"[{i + 1}/{len(files)}] {top}: {tag}", flush=True)

    # write the failing-module list for gen_candidate_bitstream --exclude
    fails = [json.loads(l)["module"] for l in open(args.out)
             if not json.loads(l).get("compiled")]
    with open(args.out + ".fails", "w") as f:
        f.write("\n".join(sorted(set(fails))) + "\n")
    print(f"\ndone: {n_ok} synthesized, {n_fail} failed this run. "
          f"{len(set(fails))} total failures -> {args.out}.fails")


if __name__ == "__main__":
    main()
