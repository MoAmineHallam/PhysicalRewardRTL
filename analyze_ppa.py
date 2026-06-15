#!/usr/bin/env python3
"""
analyze_ppa.py  -  Does functionally-EQUIVALENT RTL differ in physical quality?

Joins run_ppa.py's ppa.jsonl (timing/area/power per candidate) with the
functional reward in dataset.jsonl, keeps only functionally-correct candidates
(reward >= --min-reward), and reports the PPA SPREAD within each design.

If correct candidates of the same design differ meaningfully in Fmax / area,
that spread is the headroom an RL-PPA approach can exploit -- the motivating
result for the supervisor's PPA-optimization direction (and the silicon-Fmax
reward, the only sim-impossible signal). If they're all identical, there's
nothing to optimize.

Usage:
    python analyze_ppa.py --ppa rtl/cand_batches/ppa.jsonl --dataset dataset.jsonl
"""

import json
import argparse
import collections

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ppa", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--min-reward", type=float, default=0.999,
                    help="only candidates at/above this functional reward")
    args = ap.parse_args()

    rew = collections.defaultdict(list)
    fam = {}
    for line in open(args.dataset):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        rew[r["design"]].append(r["reward"])
        fam[r["design"]] = r.get("family", "?")

    rows, n_synth, n_fail = [], 0, 0
    for line in open(args.ppa):
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if not p.get("compiled"):
            n_fail += 1
            continue
        n_synth += 1
        mod = p["module"]
        try:
            idx = int(mod[1:].split("_", 1)[0])
            design = mod[1:].split("_", 1)[1]
            r = rew[design][idx]
        except (ValueError, KeyError, IndexError):
            continue
        if r < args.min_reward:
            continue
        rows.append({**p, "design": design, "family": fam.get(design, "?")})

    by = collections.defaultdict(list)
    for r in rows:
        by[r["design"]].append(r)
    multi = {d: rs for d, rs in by.items() if len(rs) >= 2}

    print(f"PPA: {n_synth} synthesized, {n_fail} failed.")
    print(f"functionally-correct (reward>={args.min_reward}) & synthesized: "
          f"{len(rows)} across {len(by)} designs")
    print(f"designs with >=2 correct candidates (spread measurable): {len(multi)}")
    if not multi:
        print("no design has 2+ correct synthesized candidates -- run more.")
        return

    fspreads, lspreads = [], []
    table = []
    for d, rs in multi.items():
        fmax = [x["fmax_mhz"] for x in rs]
        lut = [x["lut"] for x in rs]
        pw = [x.get("power_w", 0.0) for x in rs]
        fspread = max(fmax) - min(fmax)
        lspread = max(lut) - min(lut)
        fspreads.append(fspread)
        lspreads.append(lspread)
        table.append((d, rs[0]["family"], len(rs), min(fmax), max(fmax),
                      fspread, min(lut), max(lut), lspread,
                      min(pw), max(pw)))

    print(f"\nmean Fmax spread among correct candidates: "
          f"{np.mean(fspreads):.1f} MHz  (max {np.max(fspreads):.1f})")
    print(f"mean LUT  spread among correct candidates: "
          f"{np.mean(lspreads):.1f}      (max {np.max(lspreads):.0f})")

    print("\nlargest Fmax spread (functionally-identical, physically different):")
    print(f"{'design':16s} {'fam':12s} {'n':>2s} {'Fmax_min':>8s} "
          f"{'Fmax_max':>8s} {'dF':>6s} {'LUT_min':>7s} {'LUT_max':>7s} {'dLUT':>5s}")
    for t in sorted(table, key=lambda x: -x[5])[:25]:
        d, f, n, fmn, fmx, df, lmn, lmx, dl, pmn, pmx = t
        print(f"{d:16s} {f:12s} {n:2d} {fmn:8.1f} {fmx:8.1f} {df:6.1f} "
              f"{lmn:7d} {lmx:7d} {dl:5d}")


if __name__ == "__main__":
    main()
