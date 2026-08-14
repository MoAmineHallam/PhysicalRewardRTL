#!/usr/bin/env python3
"""
train_rf_struct.py  -  train and freeze the rf_struct reward.

The reward is a RandomForestRegressor over the 15 CANONICAL structural features
(canonicalize.STRUCT_FEATURES), predicting log(Fmax). Canonicalisation is the
point: the deployed MLP read `n_lines`, which the policy inflated by splitting
statements across lines, so the reward rose ~281 MHz while real Fmax moved -1.
Features computed on the canonical form cannot see layout at all.

PROVENANCE, STATED PLAINLY. RandomForest was noticed while inspecting the v8
outputs, so it is a POST-HOC hypothesis. The sealed split is what tests it
prospectively. Nothing here selects an architecture or a hyperparameter: the
model class and its hyperparameters are fixed by the preregistration, and the
cross-validation this script prints is DESCRIPTIVE VALIDATION ONLY -- it reports
how the frozen choice behaves on training data and changes nothing. A selection
rule applied now could not make the hypothesis blind, and pretending otherwise
would be worse than disclosing it.

Rows come from the same directories as the deployed surrogate, with §5 held-out
and sealed designs excluded (invariant #3). Candidates the canonicaliser cannot
handle are dropped from TRAINING and logged; at REWARD time they score 0.

    python train_rf_struct.py --out rf_struct.joblib --manifest rf_rows.json
"""

import os
import json
import argparse
import collections

import numpy as np

from canonicalize import (canonicalize, struct_features, STRUCT_FEATURES,
                          Unsupported, CANON_VERSION)
from surrogate_train import load_dataset, LOGF_MIN, LOGF_MAX
import gen_sft_corpus as GSC

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN_DIRS = ["rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp",
              "rtl/fmax_d2"]

# FROZEN by the preregistration. Not searched, not tuned.
RF_KWARGS = {"n_estimators": 300, "random_state": 0, "n_jobs": -1}


def family_of(design):
    for f in ("firr", "fir", "poly", "iir", "med", "cordic"):
        if design.startswith(f):
            return f
    return "other"


def build_rows(dirs):
    """-> (X, y_log, designs, families, keys, dropped). Held-out/sealed excluded."""
    raw = load_dataset([os.path.join(HERE, d) for d in dirs])
    X, y, des, fam, keys, dropped = [], [], [], [], [], []
    for r in raw:
        if GSC.is_holdout(r["design"]):
            dropped.append({"key": r["key"], "reason": "held-out or sealed"})
            continue
        p = os.path.join(HERE, r["src"], r["mod"] + ".sv")
        if not os.path.exists(p):
            dropped.append({"key": r["key"], "reason": "source missing"})
            continue
        src = open(p, errors="replace").read()
        try:
            canon, _ = canonicalize(src, "lexical")
        except Unsupported as e:
            dropped.append({"key": r["key"], "reason": f"unsupported: {e}"})
            continue
        X.append(struct_features(canon))
        y.append(np.log(float(r["fmax"])))
        des.append(r["design"])
        fam.append(family_of(r["design"]))
        keys.append({"key": r["key"], "src": r["src"], "mod": r["mod"],
                     "design": r["design"], "fmax": float(r["fmax"])})
    return (np.asarray(X, dtype=np.float64), np.asarray(y), des, fam, keys,
            dropped)


def descriptive_cv(X, y, designs):
    """Leave-one-design-out, DESCRIPTIVE ONLY -- selects nothing.

    Reports within-design ranking quality, which is what a GRPO reward actually
    needs: only the ORDER inside a sampled group drives the gradient.
    """
    from sklearn.ensemble import RandomForestRegressor
    from scipy.stats import spearmanr

    uniq = sorted(set(designs))
    d_arr = np.asarray(designs)
    preds = np.full(len(y), np.nan)
    for d in uniq:
        te = d_arr == d
        tr = ~te
        if tr.sum() < 5 or te.sum() < 1:
            continue
        m = RandomForestRegressor(**RF_KWARGS).fit(X[tr], y[tr])
        preds[te] = m.predict(X[te])
    ok = ~np.isnan(preds)
    rho_all = spearmanr(preds[ok], y[ok]).correlation if ok.sum() > 2 else float("nan")

    within = []
    for d in uniq:
        te = (d_arr == d) & ok
        if te.sum() < 3 or len(set(np.round(y[te], 6))) < 2:
            continue
        r = spearmanr(preds[te], y[te]).correlation
        if not np.isnan(r):
            within.append((d, r, int(te.sum())))
    return rho_all, within, preds, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=TRAIN_DIRS)
    ap.add_argument("--out", default=os.path.join(HERE, "rf_struct.joblib"))
    ap.add_argument("--manifest", default=os.path.join(HERE, "rf_rows.json"))
    ap.add_argument("--no-cv", action="store_true")
    args = ap.parse_args()

    from sklearn.ensemble import RandomForestRegressor
    import joblib
    import sklearn

    X, y, des, fam, keys, dropped = build_rows(args.dirs)
    print(f"rf_struct  canon v{CANON_VERSION}  sklearn {sklearn.__version__}")
    print(f"rows: {len(y)} kept, {len(dropped)} dropped")
    print(f"designs: {len(set(des))}   features: {len(STRUCT_FEATURES)}")
    by = collections.Counter(fam)
    print("per family:", dict(sorted(by.items())))
    if len(y) == 0:
        raise SystemExit("no training rows -- check --dirs")

    if not args.no_cv:
        rho, within, _, _ = descriptive_cv(X, y, des)
        print(f"\nDESCRIPTIVE leave-one-design-out (selects nothing):")
        print(f"  pooled Spearman rho          : {rho:.3f}")
        if within:
            ws = [w for _d, w, _n in within]
            print(f"  within-design rho, mean      : {np.mean(ws):.3f} "
                  f"over {len(ws)} designs with >=3 rows and spread")
            print(f"  within-design rho, median    : {np.median(ws):.3f}")
            worst = sorted(within, key=lambda t: t[1])[:5]
            print("  worst designs                : " +
                  ", ".join(f"{d}={r:.2f}" for d, r, _n in worst))

    model = RandomForestRegressor(**RF_KWARGS).fit(X, y)
    joblib.dump({"model": model, "features": STRUCT_FEATURES,
                 "canon_version": CANON_VERSION, "log_target": True,
                 "logf_min": LOGF_MIN, "logf_max": LOGF_MAX,
                 "rf_kwargs": RF_KWARGS, "n_rows": int(len(y)),
                 "sklearn": sklearn.__version__}, args.out)

    imp = sorted(zip(STRUCT_FEATURES, model.feature_importances_),
                 key=lambda t: -t[1])
    print("\nfeature importances (descriptive):")
    for n, v in imp:
        print(f"  {n:20s} {v:.4f}")

    json.dump({"canon_version": CANON_VERSION, "sklearn": sklearn.__version__,
               "rf_kwargs": RF_KWARGS, "features": STRUCT_FEATURES,
               "dirs": args.dirs, "n_rows": int(len(y)),
               "n_designs": len(set(des)), "per_family": dict(by),
               "rows": keys, "dropped": dropped},
              open(args.manifest, "w"), indent=1)
    print(f"\nwrote {args.out} and {args.manifest}")
    print("Hash BOTH into the preregistration before training any arm.")


if __name__ == "__main__":
    main()
