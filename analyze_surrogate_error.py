#!/usr/bin/env python3
"""
analyze_surrogate_error.py  -  how wrong is the surrogate on HELD-OUT designs?

Invariant #2 says surrogate numbers are never results; this quantifies why,
from artifacts already on disk (no GPU, no Vivado, no generation).

For every (policy, design) in the 5-family held-out evaluation it pairs
  - the surrogate's prediction  (holdout_summary.json: mean/max_surr_fmax), and
  - the real post-implementation number (ppa.jsonl, count-weighted per Eq. 5),
and reports the error, the saturation rate at the [5,500] clamp, and the rank
correlation -- which is the only thing a training-time reward actually needs.

    python analyze_surrogate_error.py
"""

import os
import json
import argparse
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
V8_DIRS = [os.path.join(HERE, "rtl", d) for d in
           ("holdout_eval_v8_firfirr", "holdout_eval_v8_poly",
            "holdout_eval_v8_iirmed")]
CLAMP_HI = 500.0


def spearman(xs, ys):
    """Rank correlation without scipy."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = sum((a - mx) ** 2 for a in rx) ** 0.5
    dy = sum((b - my) ** 2 for b in ry) ** 0.5
    return num / (dx * dy) if dx and dy else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=V8_DIRS)
    args = ap.parse_args()

    pairs = []          # (policy, design, surr_mean, surr_max, real_mean, real_max)
    for d in args.dirs:
        summ = json.load(open(os.path.join(d, "holdout_summary.json")))
        mani = json.load(open(os.path.join(d, "fmax_manifest.json")))
        real = {}
        for line in open(os.path.join(d, "ppa.jsonl")):
            try:
                p = json.loads(line)
            except ValueError:
                continue
            real[p["module"]] = float(p["fmax_mhz"]) if p.get("compiled") else 0.0
        agg = defaultdict(lambda: {"wsum": 0.0, "cnt": 0, "max": 0.0})
        for mod, info in mani.items():
            f = real.get(mod, 0.0)
            a = agg[(info["policy"], info["design"])]
            a["wsum"] += f * info["count"]
            a["cnt"] += info["count"]
            a["max"] = max(a["max"], f)
        for pol, designs in summ.items():
            for des, row in designs.items():
                a = agg.get((pol, des))
                if not a or not a["cnt"] or not row["corr_pct"]:
                    continue
                pairs.append((pol, des, row["mean_surr_fmax"],
                              row["max_surr_fmax"], a["wsum"] / a["cnt"],
                              a["max"]))

    print(f"{len(pairs)} (policy, design) cells with both a surrogate "
          f"prediction and a real number\n")
    print(f"{'policy':9s} {'design':13s} {'surr_mean':>9s} {'real_mean':>9s} "
          f"{'err':>8s} {'surr_max':>8s} {'real_max':>8s}")
    print("-" * 70)
    for pol, des, sm, sx, rm, rx in sorted(pairs):
        print(f"{pol:9s} {des:13s} {sm:9.1f} {rm:9.1f} {sm - rm:+8.1f} "
              f"{sx:8.1f} {rx:8.1f}")

    print("\n" + "=" * 70)
    for pol in sorted({p for p, *_ in pairs}):
        sub = [p for p in pairs if p[0] == pol]
        sm = [p[2] for p in sub]
        rm = [p[4] for p in sub]
        err = [a - b for a, b in zip(sm, rm)]
        sat = sum(1 for p in sub if p[3] >= CLAMP_HI - 1e-6)
        print(f"{pol:9s} n={len(sub):3d}  mean surrogate {sum(sm)/len(sm):6.1f} "
              f"vs real {sum(rm)/len(rm):6.1f}  "
              f"bias {sum(err)/len(err):+6.1f}  "
              f"MAE {sum(abs(e) for e in err)/len(err):5.1f}  "
              f"spearman {spearman(sm, rm):+.3f}  "
              f"clamped {sat}/{len(sub)}")
    allsm = [p[2] for p in pairs]
    allrm = [p[4] for p in pairs]
    print(f"\nOVERALL spearman(surrogate_mean, real_mean) = "
          f"{spearman(allsm, allrm):+.3f}")
    print(f"cells whose surrogate MAX sits exactly on the {CLAMP_HI:.0f} MHz "
          f"clamp: {sum(1 for p in pairs if p[3] >= CLAMP_HI - 1e-6)}/{len(pairs)}")
    print("""
Reading: a training-time reward only needs to RANK candidates, so the Spearman
figure is the one that licenses using the surrogate inside GRPO. The bias and
MAE are why the same numbers must never appear as reported frequencies, and the
clamp count is the concrete form of that failure -- once predictions pile up on
the ceiling the reward cannot distinguish a fast design from a faster one.""")


if __name__ == "__main__":
    main()
