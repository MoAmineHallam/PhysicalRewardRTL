#!/usr/bin/env python3
"""
surrogate_arch_ablation.py  -  is the reward collapse a property of OUR
predictor, or of learned physical rewards?

The obvious reviewer objection to the reward-validity result is that our
surrogate is a twelve-feature lexical MLP: a weak model extrapolates badly
off-support, which is unsurprising. This script answers it without retraining a
policy, because the off-support distribution ALREADY EXISTS as stored artifacts.

    train on : the surrogate's own labelled rows (the pre-optimization
               distribution -- supervised-era designs, held-out designs excluded
               by invariant #3)
    test on  : the held-out candidates the OPTIMIZED policy produced, each with
               a real post-implementation Vivado frequency

That is exactly the endpoint measurement (bias, saturated cells) the paper
reports for the twelve-feature MLP, so running it per architecture asks whether
a stronger or differently-shaped predictor would have survived where ours broke.

Architectures span two axes, because "weak model" is ambiguous between them:
  same features, different model class .. mlp12, gbm12, rf12, knn12
  richer features, strong model ........ ngram_ridge, ngram_gbm  (character
                                         n-grams over the RTL text: thousands of
                                         features instead of twelve)

    python surrogate_arch_ablation.py
    python surrogate_arch_ablation.py --repeats 5      # error bars on the MLP

Reading the result: if every architecture over-predicts the optimized policy by
a large margin while predicting the supervised policy well, the failure is a
property of the DISTRIBUTION SHIFT, not of the model class, and the paper's
claim generalises. If some architecture is well-calibrated on the optimized
candidates, that architecture is the fix, and the paper must say so.
"""

import os
import re
import json
import argparse
import collections

import numpy as np

from surrogate_train import extract_features, load_dataset, base_design, spearman

HERE = os.path.dirname(os.path.abspath(__file__))

TRAIN_DIRS = ["rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp", "rtl/fmax_d2"]
TEST_DIRS = ["rtl/holdout_eval_v8_firfirr", "rtl/holdout_eval_v8_poly",
             "rtl/holdout_eval_v8_iirmed"]

CLAMP_LO, CLAMP_HI = 5.0, 500.0          # the reward's own clamp, in MHz


# ------------------------------------------------------------------ data
def read_train(dirs):
    """Labelled rows + their raw RTL text. load_dataset already enforces the
    held-out exclusion (invariant #3); we re-read the text for n-gram models."""
    rows = load_dataset([os.path.join(HERE, d) for d in dirs])
    out = []
    for r in rows:
        p = r.get("path") or os.path.join(r["src"], r["mod"] + ".sv")
        if not os.path.exists(p):
            continue
        out.append({"txt": open(p, errors="replace").read(),
                    "feats": r["feats"], "fmax": r["fmax"], "design": r["design"]})
    return out


def read_test(dirs):
    """Held-out candidates with a REAL measured frequency, tagged by policy."""
    out = []
    for d in dirs:
        dd = os.path.join(HERE, d)
        mani = json.load(open(os.path.join(dd, "fmax_manifest.json")))
        for line in open(os.path.join(dd, "ppa.jsonl")):
            try:
                p = json.loads(line)
            except ValueError:
                continue
            mod = p.get("module")
            if not p.get("compiled") or mod not in mani:
                continue
            f = os.path.join(dd, mod + ".sv")
            if not os.path.exists(f):
                continue
            i = mani[mod]
            txt = open(f, errors="replace").read()
            out.append({"txt": txt, "feats": extract_features(txt),
                        "fmax": float(p["fmax_mhz"]), "policy": i["policy"],
                        "design": i["design"], "count": i["count"]})
    return out


# ------------------------------------------------------------ architectures
def fit_mlp(Xtr, ytr, Xte, seed=0):
    """The paper's predictor: 12 features, 32-32 MLP, Adam, MSE on log-Fmax."""
    import torch
    import torch.nn as nn
    torch.manual_seed(seed)
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xt = torch.tensor((Xtr - mu) / sd, dtype=torch.float32)
    yt = torch.tensor(ytr, dtype=torch.float32).view(-1, 1)
    net = nn.Sequential(nn.Linear(Xtr.shape[1], 32), nn.ReLU(),
                        nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))
    opt = torch.optim.Adam(net.parameters(), lr=1e-2)
    for _ in range(300):
        opt.zero_grad()
        ((net(Xt) - yt) ** 2).mean().backward()
        opt.step()
    with torch.no_grad():
        return net(torch.tensor((Xte - mu) / sd,
                                dtype=torch.float32)).numpy().ravel()


def fit_sklearn(model, Xtr, ytr, Xte):
    model.fit(Xtr, ytr)
    return model.predict(Xte)


def architectures(repeats):
    from sklearn.ensemble import (GradientBoostingRegressor,
                                  RandomForestRegressor)
    from sklearn.neighbors import KNeighborsRegressor
    from sklearn.linear_model import RidgeCV
    from sklearn.pipeline import make_pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer

    def ngram(est):
        # character n-grams: thousands of features, no hand-engineering, and
        # able to see any lexical pattern the twelve features encode plus many
        # they do not.
        return make_pipeline(
            TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                            min_df=2, max_features=20000, sublinear_tf=True),
            est)

    return [
        ("mlp12 (paper's)", "feats", None),          # handled specially
        ("gbm12", "feats",
         lambda: GradientBoostingRegressor(random_state=0)),
        ("rf12", "feats",
         lambda: RandomForestRegressor(n_estimators=300, random_state=0,
                                       n_jobs=-1)),
        ("knn12", "feats",
         lambda: KNeighborsRegressor(n_neighbors=5)),
        ("ngram_ridge", "text",
         lambda: ngram(RidgeCV(alphas=np.logspace(-2, 3, 20)))),
        ("ngram_gbm", "text",
         lambda: ngram(GradientBoostingRegressor(random_state=0))),
    ]


# ------------------------------------------------------------------ scoring
def cellwise(test, pred_mhz):
    """Count-weighted per (policy, design) cell, matching the paper's Eq. (5)."""
    agg = collections.defaultdict(lambda: {"pw": 0.0, "rw": 0.0, "c": 0})
    for t, p in zip(test, pred_mhz):
        a = agg[(t["policy"], t["design"])]
        a["pw"] += p * t["count"]
        a["rw"] += t["fmax"] * t["count"]
        a["c"] += t["count"]
    out = collections.defaultdict(list)
    for (pol, _), a in agg.items():
        out[pol].append((a["pw"] / a["c"], a["rw"] / a["c"]))
    return out


def report(name, test, pred_log):
    pred = np.exp(np.clip(pred_log, np.log(CLAMP_LO), np.log(CLAMP_HI)))
    cells = cellwise(test, pred)
    lines = []
    for pol in ("sft", "grpo", "bestof8", "base"):
        if pol not in cells:
            continue
        pr = np.array([c[0] for c in cells[pol]])
        rl = np.array([c[1] for c in cells[pol]])
        sat = int((pr >= CLAMP_HI - 1).sum())
        lines.append((pol, float((pr - rl).mean()), sat, len(pr),
                      float(spearman(pr, rl))))
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3,
                    help="restarts for the stochastic MLP arm")
    ap.add_argument("--out", default=os.path.join(HERE, "arch_ablation.json"))
    args = ap.parse_args()

    train = read_train(TRAIN_DIRS)
    test = read_test(TEST_DIRS)
    print(f"train: {len(train)} labelled rows (held-out designs excluded)")
    print(f"test : {len(test)} held-out candidates with real Vivado Fmax")
    print(f"       policies: "
          f"{dict(collections.Counter(t['policy'] for t in test))}\n")

    Xtr = np.array([r["feats"] for r in train], float)
    ytr = np.log(np.array([r["fmax"] for r in train], float))
    Xte = np.array([t["feats"] for t in test], float)
    Ttr = [r["txt"] for r in train]
    Tte = [t["txt"] for t in test]

    print(f"{'architecture':16s} {'policy':8s} {'bias MHz':>10s} "
          f"{'saturated':>11s} {'rho':>7s}")
    print("-" * 60)
    results = {}
    for name, space, mk in architectures(args.repeats):
        if space == "feats" and mk is None:
            preds = [fit_mlp(Xtr, ytr, Xte, seed=s) for s in range(args.repeats)]
            pred_log = np.mean(preds, axis=0)
        elif space == "feats":
            pred_log = fit_sklearn(mk(), Xtr, ytr, Xte)
        else:
            pred_log = fit_sklearn(mk(), Ttr, ytr, Tte)
        rows = report(name, test, pred_log)
        results[name] = rows
        for i, (pol, bias, sat, n, rho) in enumerate(rows):
            print(f"{name if i == 0 else '':16s} {pol:8s} {bias:+10.1f} "
                  f"{sat:6d}/{n:<4d} {rho:7.3f}")
        print()

    json.dump(results, open(args.out, "w"), indent=1)
    print(f"wrote {args.out}\n")
    print("If every architecture over-predicts the OPTIMIZED policy by a large")
    print("margin while tracking the SUPERVISED one, the failure belongs to the")
    print("distribution shift and not to the model class -- which is the")
    print("generality the reviewer will ask for. If one architecture is")
    print("well-calibrated on the optimized cells, that architecture is the fix")
    print("and the paper must report it as such.")


if __name__ == "__main__":
    main()
