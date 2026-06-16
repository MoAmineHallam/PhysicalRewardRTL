#!/usr/bin/env python3
"""
bestofn_ppa.py  -  Hardware-PPA-guided best-of-N reranking gain.

Offline RL toward PPA (grpo_train_v4) degraded functional correctness, because
its reward had no correctness term -- the model just memorised lean candidates.
The robust alternative: generate N, keep only the functionally-correct ones,
and pick the leanest. This can never hurt correctness (it selects among correct
outputs only) and directly captures the PPA headroom.

This reads run_ppa's ppa.jsonl for a model's *correct* generations (from
eval_ppa_gen) + the eval_manifest, then per design compares:
  - mean LUT/Fmax over all correct gens  (= expected single greedy/sampled output)
  - best-of-N LUT/Fmax (min LUT / max Fmax among the correct gens)
The aggregate gap is the reranking gain at no correctness cost.

Usage:
  python bestofn_ppa.py --ppa rtl/ppa_eval/base_ppa.jsonl \
                        --manifest rtl/ppa_eval/base/eval_manifest.json
"""

import json
import argparse
import collections

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ppa", required=True)
    ap.add_argument("--manifest", required=True)
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
            by[m["design"]].append(p)

    multi = {d: rs for d, rs in by.items() if len(rs) >= 2}
    print(f"designs with >=2 correct synthesized gens: {len(multi)} "
          f"(of {len(by)} total)")
    if not multi:
        print("not enough correct synthesized generations to rerank.")
        return

    # per design: mean (random pick) vs best-of-N (min LUT / max Fmax)
    mean_lut, best_lut, mean_fmax, best_fmax = [], [], [], []
    rows = []
    for d, rs in multi.items():
        lut = [x["lut"] for x in rs]
        fmax = [x["fmax_mhz"] for x in rs]
        mean_lut.append(np.mean(lut)); best_lut.append(min(lut))
        mean_fmax.append(np.mean(fmax)); best_fmax.append(max(fmax))
        rows.append((d, len(rs), np.mean(lut), min(lut),
                     np.mean(fmax), max(fmax)))

    ml, bl = float(np.mean(mean_lut)), float(np.mean(best_lut))
    mf, bf = float(np.mean(mean_fmax)), float(np.mean(best_fmax))
    print(f"\nAcross {len(multi)} designs (averaged):")
    print(f"  LUT : mean-of-sample {ml:.2f}  ->  best-of-N {bl:.2f}   "
          f"({100*(ml-bl)/ml:+.1f}% area)")
    print(f"  Fmax: mean-of-sample {mf:.1f}  ->  best-of-N {bf:.1f} MHz "
          f"({100*(bf-mf)/mf:+.1f}% speed)")

    print("\nbiggest per-design area win (mean LUT -> best-of-N LUT):")
    rows.sort(key=lambda r: -(r[2] - r[3]))
    print(f"{'design':16s} {'n':>2s} {'meanLUT':>8s} {'bestLUT':>8s} "
          f"{'meanFmax':>9s} {'bestFmax':>9s}")
    for d, n, mlu, blu, mfx, bfx in rows[:20]:
        print(f"{d:16s} {n:2d} {mlu:8.2f} {blu:8d} {mfx:9.1f} {bfx:9.1f}")


if __name__ == "__main__":
    main()
