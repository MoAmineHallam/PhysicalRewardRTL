#!/usr/bin/env python3
"""
analyze_policy_fmax.py  -  count-weighted REAL Fmax and correctness per policy.

The single table the paper's main claim rests on, computed from committed
artifacts only: the manifest gives each distinct candidate's sample
multiplicity, ppa.jsonl gives its post-implementation frequency, and Eq. (5)
weights the second by the first.

    python analyze_policy_fmax.py                          # 5-family 30-design set
    python analyze_policy_fmax.py --dirs rtl/holdout_eval_ablate_const
    python analyze_policy_fmax.py --dirs rtl/holdout_eval_v9

Two statistics are printed and they answer different questions:

  meanF(correct)  expected frequency of a sample GIVEN it is correct. Does not
                  penalise a policy for failing often, so it must always be
                  read next to the correctness column.
  meanF(penalised) expected frequency of a sample, scoring incorrect samples
                  0 MHz. This is the equal-sample-cost number and the one to
                  lead with, because it cannot be gamed by a policy that gets
                  fast only on the rare occasions it is right.
"""

import os
import json
import argparse
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
V8_DIRS = [os.path.join(HERE, "rtl", d) for d in
           ("holdout_eval_v8_firfirr", "holdout_eval_v8_poly",
            "holdout_eval_v8_iirmed")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=V8_DIRS)
    args = ap.parse_args()

    # (policy, regime) -> weighted sum, correct-sample count, total samples
    agg = collections.defaultdict(lambda: {"w": 0.0, "c": 0, "tot": 0})
    designs = collections.defaultdict(set)
    for d in args.dirs:
        mani = json.load(open(os.path.join(d, "fmax_manifest.json")))
        real = {}
        for line in open(os.path.join(d, "ppa.jsonl")):
            try:
                p = json.loads(line)
            except ValueError:
                continue
            real[p["module"]] = (float(p["fmax_mhz"])
                                 if p.get("compiled") else 0.0)
        # total samples per (policy, design) is n, counted once per design
        seen = set()
        for mod, i in mani.items():
            key = (i["policy"], i["regime"])
            if mod in real:
                agg[key]["w"] += real[mod] * i["count"]
                agg[key]["c"] += i["count"]
            if (i["policy"], i["design"]) not in seen:
                seen.add((i["policy"], i["design"]))
                agg[key]["tot"] += i["n"]
                designs[i["policy"]].add(i["design"])

    print(f"{'policy':9s} {'regime':7s} {'meanF(correct)':>15s} "
          f"{'meanF(penalised)':>17s} {'correct%':>9s} {'cands':>7s}")
    print("-" * 70)
    tot = collections.defaultdict(lambda: {"w": 0.0, "c": 0, "tot": 0})
    for (pol, reg), a in sorted(agg.items()):
        t = tot[pol]
        t["w"] += a["w"]; t["c"] += a["c"]; t["tot"] += a["tot"]
        mc = a["w"] / a["c"] if a["c"] else 0.0
        mp = a["w"] / a["tot"] if a["tot"] else 0.0
        print(f"{pol:9s} {reg:7s} {mc:15.1f} {mp:17.1f} "
              f"{100.0 * a['c'] / a['tot']:8.1f}% {a['c']:7d}")
    print("-" * 70)
    for pol, t in sorted(tot.items()):
        print(f"{pol:9s} {'ALL':7s} {t['w'] / t['c']:15.1f} "
              f"{t['w'] / t['tot']:17.1f} "
              f"{100.0 * t['c'] / t['tot']:8.1f}% {t['c']:7d}"
              f"   ({len(designs[pol])} designs)")
    print("\nA policy whose meanF(correct) is high but meanF(penalised) is low "
          "is fast only\nwhen it happens to be right. Report both.")


if __name__ == "__main__":
    main()
