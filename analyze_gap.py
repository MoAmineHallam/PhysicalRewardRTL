#!/usr/bin/env python3
"""
analyze_gap.py  -  The headline of the simulation/silicon reward-gap study.

Reads score_hw_candidates.py's cand_gap.jsonl (sim_reward vs hw_reward per
candidate) and reports:
  - the disagreement rate (|sim - hw| over a threshold) -- the number that
    says how often the standard simulation reward is wrong about silicon;
  - direction: sim UNDER-rewards (sim<hw, e.g. reset/init masked as X in
    simulation but GSR-correct on FPGA) vs sim OVER-rewards (sim>hw);
  - per-family breakdown and the largest divergences, to categorise causes.

Usage:
    python analyze_gap.py rtl/cand_batches/cand_gap.jsonl
    python analyze_gap.py cand_gap.jsonl --threshold 0.1
"""

import sys
import json
import argparse
import collections


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("gap")
    ap.add_argument("--threshold", type=float, default=0.1,
                    help="|sim - hw| above this counts as a disagreement")
    args = ap.parse_args()

    rows = []
    for line in open(args.gap):
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    if not rows:
        print("no records")
        return

    n = len(rows)
    disagree = [r for r in rows if abs(r["gap"]) > args.threshold]
    under = [r for r in rows if r["gap"] < -args.threshold]   # sim < hw
    over = [r for r in rows if r["gap"] > args.threshold]      # sim > hw
    mean_abs = sum(abs(r["gap"]) for r in rows) / n

    print(f"candidates scored on silicon: {n}")
    print(f"mean |sim - hw| gap:          {mean_abs:.3f}")
    print(f"disagreements (|gap|>{args.threshold}):    "
          f"{len(disagree)} ({100*len(disagree)/n:.1f}%)")
    print(f"  sim UNDER-rewards (sim<hw): {len(under)} "
          f"({100*len(under)/n:.1f}%)  <- reset/init class predicted here")
    print(f"  sim OVER-rewards  (sim>hw): {len(over)} "
          f"({100*len(over)/n:.1f}%)  <- latch/race/timing class")

    fam = collections.defaultdict(list)
    for r in rows:
        fam[r["family"]].append(r)
    print(f"\n{'family':16s} {'n':>4s} {'mean|gap|':>9s} {'disagree%':>9s}")
    for f in sorted(fam, key=lambda f: -sum(abs(x['gap'])
                                            for x in fam[f]) / len(fam[f])):
        rs = fam[f]
        ma = sum(abs(x["gap"]) for x in rs) / len(rs)
        dr = 100 * sum(abs(x["gap"]) > args.threshold for x in rs) / len(rs)
        print(f"{f:16s} {len(rs):4d} {ma:9.3f} {dr:9.1f}")

    print("\nlargest sim-UNDER-rewards (silicon right, simulation wrong):")
    for r in sorted(rows, key=lambda r: r["gap"])[:15]:
        print(f"   {r['module']:22s} fam={r['family']:12s} "
              f"sim={r['sim_reward']:.3f} hw={r['hw_reward']:.3f} "
              f"gap={r['gap']:+.3f}")
    print("\nlargest sim-OVER-rewards (simulation too generous):")
    for r in sorted(rows, key=lambda r: -r["gap"])[:15]:
        print(f"   {r['module']:22s} fam={r['family']:12s} "
              f"sim={r['sim_reward']:.3f} hw={r['hw_reward']:.3f} "
              f"gap={r['gap']:+.3f}")


if __name__ == "__main__":
    main()
