#!/usr/bin/env python3
"""
check_a_orderability.py  -  does canonicalisation destroy the information the
reward needs to ORDER candidates?

THE GO/NO-GO before any GPU time. Canonicalisation removes layout. It must not
also remove the distinctions that separate a fast implementation from a slow
one, because a reward that cannot order candidates supplies no gradient no
matter how invariant it is.

The naive test -- "what fraction of rows collapse?" -- is the wrong criterion.
Alpha-equivalent and trivia-only duplicates SHOULD collapse; a large collapse
rate is the tool working. The decision statistic is instead:

    MATERIALLY UNORDERABLE PAIR RATE

    denominator  within-design pairs of labelled training rows whose MEASURED
                 Fmax differs by more than max(5 MHz, 2%) -- i.e. pairs a reward
                 genuinely needs to tell apart
    numerator    those pairs whose canonical FEATURE VECTORS are identical --
                 i.e. pairs the reward provably cannot tell apart

A second, more serious statistic is reported separately:

    UNSAFE SEMANTIC MERGE

    within-design pairs whose canonical TEXT is byte-identical yet whose
    measured Fmax differs materially. Identical canonical text should mean
    identical hardware, so this is either a canonicaliser defect that merged two
    different circuits, or tool noise. Any non-zero count must be inspected
    individually, never averaged away.

PREREGISTERED THRESHOLDS (fixed before running, per external review):
    unsafe semantic merges ........ exactly 0
    unorderable rate, overall ..... <= 10%
    unorderable rate, any family .. <= 25%
    rejection rate ................ <= 1%

Raw unique-row retention is reported for information and is explicitly NOT a
decision criterion.

    python check_a_orderability.py --backend lexical --out check_a.json
"""

import os
import json
import argparse
import collections
import itertools

import numpy as np

from canonicalize import (canonicalize, canon_hash, struct_features,
                          STRUCT_FEATURES, Unsupported, CANON_VERSION)
from surrogate_train import load_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN_DIRS = ["rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp",
              "rtl/fmax_d2"]

# thresholds are constants so that changing one is a visible diff, not a habit
MAX_UNSAFE = 0
MAX_RATE_OVERALL = 0.10
MAX_RATE_FAMILY = 0.25
MAX_REJECT = 0.01


def family_of(design):
    for f in ("firr", "fir", "poly", "iir", "med", "cordic"):
        if design.startswith(f):
            return f
    return "other"


def material(a, b):
    """Is this pair one the reward genuinely has to separate?"""
    return abs(a - b) > max(5.0, 0.02 * max(a, b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="lexical",
                    choices=["auto", "yosys", "lexical"])
    ap.add_argument("--dirs", nargs="*", default=TRAIN_DIRS)
    ap.add_argument("--out", default=os.path.join(HERE, "check_a.json"))
    args = ap.parse_args()

    rows = load_dataset([os.path.join(HERE, d) for d in args.dirs])
    print(f"check_a  canonicaliser v{CANON_VERSION}  backend={args.backend}")
    print(f"training rows (held-out designs already excluded): {len(rows)}")

    kept, rejected = [], []
    for r in rows:
        p = os.path.join(HERE, r["src"], r["mod"] + ".sv")
        if not os.path.exists(p):
            continue
        src = open(p, errors="replace").read()
        try:
            c, be = canonicalize(src, args.backend)
        except Unsupported as e:
            rejected.append({"key": r["key"], "reason": str(e)})
            continue
        kept.append({"key": r["key"], "design": r["design"],
                     "family": family_of(r["design"]), "fmax": float(r["fmax"]),
                     "canon": c, "hash": canon_hash(c),
                     "feats": tuple(struct_features(c))})

    n = len(kept) + len(rejected)
    rej_rate = len(rejected) / n if n else 0.0
    print(f"canonicalised {len(kept)}, rejected {len(rejected)} "
          f"({100 * rej_rate:.2f}%)")

    # ---- information-only: retention ------------------------------------
    print(f"\nretention (INFORMATION ONLY, not a decision criterion)")
    print(f"  distinct canonical texts   : {len({k['hash'] for k in kept})}"
          f" / {len(kept)}")
    print(f"  distinct feature vectors   : {len({k['feats'] for k in kept})}"
          f" / {len(kept)}")

    # ---- the decision statistics ----------------------------------------
    by_design = collections.defaultdict(list)
    for k in kept:
        by_design[k["design"]].append(k)

    fam = collections.defaultdict(lambda: {"mat": 0, "unord": 0})
    unsafe = []
    tot_mat = tot_unord = 0
    for design, ks in by_design.items():
        for a, b in itertools.combinations(ks, 2):
            if not material(a["fmax"], b["fmax"]):
                continue
            tot_mat += 1
            fam[a["family"]]["mat"] += 1
            if a["feats"] == b["feats"]:
                tot_unord += 1
                fam[a["family"]]["unord"] += 1
            if a["hash"] == b["hash"]:
                unsafe.append({"design": design, "a": a["key"], "b": b["key"],
                               "fmax_a": a["fmax"], "fmax_b": b["fmax"]})

    rate = tot_unord / tot_mat if tot_mat else 0.0
    print(f"\nmaterially different within-design pairs : {tot_mat}")
    print(f"  of which UNORDERABLE (identical features): {tot_unord} "
          f"({100 * rate:.1f}%)")
    print(f"\n{'family':8s} {'material':>9s} {'unorderable':>12s} {'rate':>7s}")
    fam_rates = {}
    for f, d in sorted(fam.items()):
        r = d["unord"] / d["mat"] if d["mat"] else 0.0
        fam_rates[f] = r
        print(f"{f:8s} {d['mat']:9d} {d['unord']:12d} {100 * r:6.1f}%")

    print(f"\nUNSAFE SEMANTIC MERGES (identical canonical text, materially "
          f"different Fmax): {len(unsafe)}")
    for u in unsafe[:10]:
        print(f"   {u['design']:12s} {u['fmax_a']:7.1f} vs {u['fmax_b']:7.1f} MHz"
              f"   {os.path.basename(u['a'])} / {os.path.basename(u['b'])}")

    # ---- verdict ---------------------------------------------------------
    worst_fam = max(fam_rates.values()) if fam_rates else 0.0
    checks = [
        ("unsafe semantic merges == 0", len(unsafe) <= MAX_UNSAFE,
         f"{len(unsafe)}"),
        (f"overall unorderable <= {100 * MAX_RATE_OVERALL:.0f}%",
         rate <= MAX_RATE_OVERALL, f"{100 * rate:.1f}%"),
        (f"per-family unorderable <= {100 * MAX_RATE_FAMILY:.0f}%",
         worst_fam <= MAX_RATE_FAMILY, f"{100 * worst_fam:.1f}% worst"),
        (f"rejection rate <= {100 * MAX_REJECT:.0f}%",
         rej_rate <= MAX_REJECT, f"{100 * rej_rate:.2f}%"),
    ]
    print("\n" + "=" * 62)
    ok = True
    for name, passed, val in checks:
        ok &= passed
        print(f"  {name:38s} {val:>10s}  {'PASS' if passed else 'FAIL'}")
    print("=" * 62)
    print(f"CHECK A: {'GO' if ok else 'NO-GO'}")
    if not ok:
        print("\nNO-GO means the canonical representation cannot order the "
              "training\ndata well enough to be a reward. Fix the "
              "representation -- do NOT\nproceed to GRPO and do not weaken "
              "these thresholds after seeing them.")

    json.dump({"canon_version": CANON_VERSION, "backend": args.backend,
               "n_rows": n, "n_kept": len(kept), "rejected": rejected,
               "rejection_rate": rej_rate,
               "distinct_canonical": len({k["hash"] for k in kept}),
               "distinct_features": len({k["feats"] for k in kept}),
               "material_pairs": tot_mat, "unorderable_pairs": tot_unord,
               "unorderable_rate": rate,
               "family_rates": fam_rates, "unsafe_merges": unsafe,
               "thresholds": {"unsafe": MAX_UNSAFE,
                              "overall": MAX_RATE_OVERALL,
                              "family": MAX_RATE_FAMILY,
                              "reject": MAX_REJECT},
               "verdict": "GO" if ok else "NO-GO",
               "features": STRUCT_FEATURES},
              open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
