#!/usr/bin/env python3
"""
compare_eval.py  -  SFT vs GRPO on REAL Vivado Fmax (the Stage-4 verdict).

Reads compare_policies' manifest (module -> policy/design/count) + run_ppa's
ppa.jsonl, and per design reports, for each policy, the correctness rate and the
sample-frequency-weighted REAL Fmax (each distinct design weighted by how often
the policy sampled it). The GRPO win condition: correctness holds AND mean real
Fmax shifts up vs SFT. Also flags surrogate gaming by comparing to the surrogate
summary if present.

    python compare_eval.py --dir rtl/policy_cmp
"""

import os
import json
import argparse
from collections import defaultdict

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="rtl/policy_cmp")
    args = ap.parse_args()

    mani = json.load(open(os.path.join(args.dir, "fmax_manifest.json")))
    fmax = {}
    for line in open(os.path.join(args.dir, "ppa.jsonl")):
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if p.get("compiled"):
            fmax[p["module"]] = float(p.get("fmax_mhz", 0.0))

    # per (policy, design): weighted real Fmax + correct samples
    agg = defaultdict(lambda: {"wsum": 0.0, "cnt": 0, "max": 0.0, "n": 0})
    for mod, info in mani.items():
        if mod not in fmax:
            continue
        key = (info["policy"], info["design"])
        a = agg[key]
        a["wsum"] += info["count"] * fmax[mod]
        a["cnt"] += info["count"]
        a["max"] = max(a["max"], fmax[mod])
        a["n"] = info["n"]

    designs = sorted({d for (_, d) in agg})
    print(f"{'design':12s} | {'SFT corr% meanF maxF':>22s} | "
          f"{'GRPO corr% meanF maxF':>22s} | {'dMeanF':>7s}")
    print("-" * 78)
    s_means, g_means = [], []
    for d in designs:
        s, g = agg.get(("sft", d)), agg.get(("grpo", d))
        def fmt(a):
            if not a or a["cnt"] == 0:
                return 0.0, 0.0, 0.0
            return 100.0*a["cnt"]/a["n"], a["wsum"]/a["cnt"], a["max"]
        sc, sm, sx = fmt(s); gc, gm, gx = fmt(g)
        s_means.append(sm); g_means.append(gm)
        print(f"{d:12s} | {sc:6.0f} {sm:7.1f} {sx:6.0f} | "
              f"{gc:6.0f} {gm:7.1f} {gx:6.0f} | {gm-sm:+7.1f}")
    print("-" * 78)
    sm_, gm_ = float(np.mean(s_means)), float(np.mean(g_means))
    print(f"mean real Fmax across designs: SFT {sm_:.1f} -> GRPO {gm_:.1f} "
          f"({gm_-sm_:+.1f} MHz, {100*(gm_-sm_)/sm_:+.0f}%)")

    # gaming check: surrogate-claimed vs real max
    sp = os.path.join(args.dir, "surrogate_summary.json")
    if os.path.exists(sp):
        summ = json.load(open(sp))
        print("\ngaming check (GRPO surrogate maxF vs REAL maxF):")
        for d in designs:
            g = agg.get(("grpo", d))
            sur = summ.get("grpo", {}).get(d, {}).get("max_surr_fmax", 0)
            real = g["max"] if g else 0
            flag = "  <-- surrogate INFLATED" if sur > real * 1.3 and real > 0 else ""
            print(f"  {d:12s} surrogate {sur:6.0f}  real {real:6.0f}{flag}")
    print("\nVERDICT: GRPO succeeds where correctness holds (corr% not down) AND "
          "GRPO meanF > SFT meanF on REAL Fmax. Surrogate-inflated rows = gaming "
          "to re-anchor (synth them, add to surrogate training, retrain).")


if __name__ == "__main__":
    main()
