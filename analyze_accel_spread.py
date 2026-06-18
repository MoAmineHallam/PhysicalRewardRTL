#!/usr/bin/env python3
"""
analyze_accel_spread.py  -  Does the base model expose Fmax headroom? (Phase-3 probe)

Reads run_ppa's ppa.jsonl for the probe candidates (gen_accel_candidates.py) +
the probe manifest, and per design reports the Fmax SPREAD among the
functionally-correct generations. That spread is the headroom the RL can
actually exploit: if the base model only ever emits one implementation per spec
(near-zero spread), silicon-Fmax RL has nothing to push on and best-of-N
reranking is the honest deliverable; if the spread is large, RL has signal.

    python analyze_accel_spread.py --ppa rtl/accel_probe/ppa.jsonl \
        --manifest rtl/accel_probe/probe_manifest.json
"""

import json
import argparse
import collections

import numpy as np

# silicon ~= 1.9x Vivado within these families (Phase-2 finding); used only to
# annotate the spread in silicon-equivalent terms.
SIL = 1.9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ppa", default="rtl/accel_probe/ppa.jsonl")
    ap.add_argument("--manifest", default="rtl/accel_probe/probe_manifest.json")
    args = ap.parse_args()

    mani = json.load(open(args.manifest))
    by = collections.defaultdict(list)
    for line in open(args.ppa):
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if not p.get("compiled"):
            continue
        m = mani.get(p["module"])
        if m:
            by[m["design"]].append(p.get("fmax_mhz", 0.0))

    if not by:
        print("no compiled probe candidates found.")
        return

    print(f"{'design':10s} {'n':>3s} {'minF':>6s} {'maxF':>6s} {'meanF':>6s} "
          f"{'std':>6s} {'spread':>7s} {'~silSpread':>10s}")
    print("-" * 64)
    spreads, rel = [], []
    for d in sorted(by):
        f = np.array(by[d], dtype=float)
        sp = float(f.max() - f.min())
        spreads.append(sp)
        if f.mean() > 0:
            rel.append(sp / f.mean())
        print(f"{d:10s} {len(f):3d} {f.min():6.1f} {f.max():6.1f} {f.mean():6.1f} "
              f"{f.std():6.1f} {sp:7.1f} {sp*SIL:10.1f}")

    med_sp = float(np.median(spreads))
    med_rel = float(np.median(rel)) if rel else 0.0
    print("-" * 64)
    print(f"median within-design Vivado Fmax spread: {med_sp:.1f} MHz "
          f"(~{med_sp*SIL:.0f} MHz silicon), {100*med_rel:.0f}% of mean")
    print("\nVERDICT:")
    if med_sp >= 15:
        print(f"  GO for RL -- the base model exposes real Fmax headroom "
              f"(median ~{med_sp:.0f} MHz Vivado / ~{med_sp*SIL:.0f} MHz silicon "
              f"between its slowest and fastest correct generations). The "
              f"correctness-gated Fmax RL can push toward the fast tail.")
    else:
        print(f"  WEAK signal -- base generations cluster at similar Fmax "
              f"(median spread {med_sp:.0f} MHz). RL-for-Fmax has little room; "
              f"prefer best-of-N reranking, or raise temperature / diversify "
              f"prompts to widen the candidate distribution before training.")


if __name__ == "__main__":
    main()
