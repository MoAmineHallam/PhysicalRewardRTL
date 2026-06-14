#!/usr/bin/env python3
"""
extract_build_fails.py  -  Harvest candidates that failed the Vivado build.

synth_check.tcl only runs synthesis, so it misses candidates that synthesize
but fail at IMPLEMENTATION (e.g. DRC MDRV-1 multiple-driver nets -- a register
driven from two places, valid-ish in simulation but physically impossible on
silicon). This scans the batch build logs, finds every candidate instance
named in an ERROR line, maps it back to its module via cand_manifest.json, and
merges the list into the exclude file.

These are themselves gap-study tier-1 results: sim-valid (often even
synth-valid) RTL that cannot be realised on hardware. The printed count is
data, not just bookkeeping.

Run from the repo root (laptop), after a build round:
    python extract_build_fails.py
    # then: regenerate with the enlarged exclude list and rebuild
"""

import os
import re
import json
import glob

OUT = os.path.join("rtl", "cand_batches")
FAILS = os.path.join(OUT, "synth.fails")


def main():
    man = json.load(open(os.path.join(OUT, "cand_manifest.json")))
    # (batch, local_sel) -> module  (instances are named u_d<local_sel>)
    bymap = {(d["batch"], d["local_sel"]): d["module"]
             for d in man["designs"]}

    culprits = set()
    logs = glob.glob(os.path.join(OUT, "out_cb*", "**", "runme.log"),
                     recursive=True)
    for log in logs:
        mb = re.search(r"out_cb(\d+)", log.replace("\\", "/"))
        if not mb:
            continue
        batch = int(mb.group(1))
        for line in open(log, errors="ignore"):
            if "ERROR" not in line:
                continue
            # implementation errors name the instance: .../u_d<sel>/...
            for sel in re.findall(r"u_d(\d+)[/ ]", line):
                mod = bymap.get((batch, int(sel)))
                if mod:
                    culprits.add(mod)
            # synth errors name the source file: cand/<module>.sv
            for mod in re.findall(r"cand[\\/]([A-Za-z0-9_]+)\.sv", line):
                culprits.add(mod)

    existing = set()
    if os.path.exists(FAILS):
        existing = {ln.strip() for ln in open(FAILS) if ln.strip()}
    merged = sorted(existing | culprits)
    with open(FAILS, "w") as f:
        f.write("\n".join(merged) + "\n")

    print(f"scanned {len(logs)} build logs")
    print(f"new build-failure candidates this scan: {len(culprits - existing)}")
    for c in sorted(culprits - existing):
        print("   ", c)
    print(f"total exclude list: {len(merged)} -> {FAILS}")


if __name__ == "__main__":
    main()
