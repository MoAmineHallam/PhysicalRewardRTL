#!/usr/bin/env python3
"""
gen_ppa_set.py  -  Extract functionally-CORRECT candidates (several per design)
from dataset.jsonl into .sv files, for the PPA-spread measurement.

The gap-study candidate pool was stratified toward BUGGY candidates, so it has
too few correct ones per design to compare their PPA. The full dataset has up
to 10 candidates/design and many designs are fully correct -- the right source
for "do functionally-equivalent designs differ physically?".

Writes <design>__c<k>.sv (module renamed to match) + ppa_set_manifest.json
(module -> {design, family}). Then: run_ppa on the dir, analyze_ppa --manifest.

Usage:
    python gen_ppa_set.py --dataset dataset.jsonl
    python gen_ppa_set.py --max-designs 40 --max-per-design 5
"""

import os
import json
import shutil
import argparse
import collections

from gen_candidate_bitstream import rename_module


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="dataset.jsonl")
    ap.add_argument("--out-dir", default=os.path.join("rtl", "ppa_set", "cand"))
    ap.add_argument("--manifest",
                    default=os.path.join("rtl", "ppa_set", "ppa_set_manifest.json"))
    ap.add_argument("--min-reward", type=float, default=0.999)
    ap.add_argument("--min-count", type=int, default=2,
                    help="keep designs with >= this many correct candidates")
    ap.add_argument("--max-per-design", type=int, default=6)
    ap.add_argument("--max-designs", type=int, default=60,
                    help="cap total designs to bound synthesis time")
    args = ap.parse_args()

    bydesign = collections.defaultdict(list)
    fam = {}
    for line in open(args.dataset):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        fam[r["design"]] = r.get("family", "?")
        if r.get("compile_ok") and r["reward"] >= args.min_reward:
            bydesign[r["design"]].append(r["rtl"])

    designs = [(d, c) for d, c in bydesign.items() if len(c) >= args.min_count]
    designs.sort(key=lambda x: -len(x[1]))           # most-correct designs first
    designs = designs[:args.max_designs]

    if os.path.isdir(args.out_dir):
        shutil.rmtree(args.out_dir)
    os.makedirs(args.out_dir, exist_ok=True)

    mani, n = {}, 0
    for d, cands in designs:
        for k, rtl in enumerate(cands[:args.max_per_design]):
            mod = f"{d}__c{k}"
            with open(os.path.join(args.out_dir, mod + ".sv"), "w") as f:
                f.write(rename_module(rtl, d, mod))
            mani[mod] = {"design": d, "family": fam.get(d, "?")}
            n += 1

    os.makedirs(os.path.dirname(args.manifest), exist_ok=True)
    json.dump(mani, open(args.manifest, "w"), indent=1)
    print(f"{len(designs)} designs with >={args.min_count} correct candidates; "
          f"wrote {n} candidate .sv -> {args.out_dir}")
    print(f"manifest -> {args.manifest}")
    print(f"next:\n"
          f"  python run_ppa.py --dir {args.out_dir} "
          f"--out rtl/ppa_set/ppa.jsonl --clk clk --period 5.0\n"
          f"  python analyze_ppa.py --ppa rtl/ppa_set/ppa.jsonl "
          f"--manifest {args.manifest}")


if __name__ == "__main__":
    main()
