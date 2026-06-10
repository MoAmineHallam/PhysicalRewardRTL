#!/usr/bin/env python3
"""
analyze_dataset.py  -  Stage 7 dataset analysis -> GRPO sampling weights.

Reads the build_dataset.py JSONL and reports, per design and per family:
mean/min/max reward, within-design reward spread (the GRPO gradient signal),
compile rate, and saturation (all candidates at 1.0 = no learning signal).

Writes design_weights.json: sampling weight per design proportional to the
within-design reward standard deviation (plus a floor so saturated designs
are still occasionally revisited).

Usage:
    python analyze_dataset.py fpga/dataset.jsonl
    python analyze_dataset.py fpga/dataset.jsonl --weights fpga/design_weights.json
"""

import json
import argparse
import collections

import numpy as np

WEIGHT_FLOOR = 0.05  # saturated designs still get sampled occasionally


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dataset")
    ap.add_argument("--weights", default="design_weights.json")
    args = ap.parse_args()

    rows = collections.defaultdict(list)
    fam_of = {}
    n_rec = 0
    for line in open(args.dataset):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        rows[r["design"]].append((r["reward"], r["compile_ok"]))
        fam_of[r["design"]] = r.get("family", "?")
        n_rec += 1

    per_design = {}
    for name, rs in rows.items():
        rew = np.array([x[0] for x in rs], dtype=float)
        per_design[name] = {
            "n": len(rew),
            "mean": float(rew.mean()),
            "std": float(rew.std()),
            "max": float(rew.max()),
            "min": float(rew.min()),
            "compile_rate": float(np.mean([x[1] for x in rs])),
            "family": fam_of[name],
        }

    sat = [n for n, d in per_design.items() if d["min"] >= 0.999]
    dead = [n for n, d in per_design.items() if d["max"] <= 0.001]
    live = [n for n, d in per_design.items() if d["std"] > 0.01]

    print(f"records: {n_rec}   designs: {len(per_design)}")
    print(f"saturated (all 1.0, no signal):   {len(sat)}")
    print(f"dead (all ~0, also no signal):    {len(dead)}")
    print(f"live (reward spread -> gradient): {len(live)}")
    all_r = np.array([r for rs in rows.values() for r, _ in rs])
    all_c = np.array([c for rs in rows.values() for _, c in rs])
    print(f"overall: mean reward {all_r.mean():.3f}, "
          f"compile rate {all_c.mean():.3f}, "
          f"perfect rate {(all_r >= 0.999).mean():.3f}")

    # per-family table
    fams = collections.defaultdict(list)
    for name, d in per_design.items():
        fams[d["family"]].append(d)
    print(f"\n{'family':16s} {'designs':>7s} {'mean':>6s} {'std':>6s} "
          f"{'comp%':>6s} {'sat%':>5s}")
    for fam in sorted(fams, key=lambda f: np.mean([d['mean'] for d in fams[f]])):
        ds = fams[fam]
        print(f"{fam:16s} {len(ds):7d} "
              f"{np.mean([d['mean'] for d in ds]):6.3f} "
              f"{np.mean([d['std'] for d in ds]):6.3f} "
              f"{100 * np.mean([d['compile_rate'] for d in ds]):6.1f} "
              f"{100 * np.mean([d['min'] >= 0.999 for d in ds]):5.1f}")

    print("\nhardest 20 designs (lowest mean reward):")
    for name in sorted(per_design, key=lambda n: per_design[n]["mean"])[:20]:
        d = per_design[name]
        print(f"   {name:16s} fam={d['family']:14s} mean={d['mean']:.3f} "
              f"std={d['std']:.3f} max={d['max']:.3f} "
              f"compile={d['compile_rate']:.2f}")

    # GRPO sampling weights: proportional to within-design std + floor
    weights = {n: max(d["std"], WEIGHT_FLOOR) for n, d in per_design.items()}
    total = sum(weights.values())
    weights = {n: w / total for n, w in weights.items()}
    json.dump({"weights": weights,
               "stats": per_design}, open(args.weights, "w"), indent=1)
    print(f"\nwrote {args.weights} ({len(weights)} designs; weight ~ reward "
          f"std, floor {WEIGHT_FLOOR})")


if __name__ == "__main__":
    main()
