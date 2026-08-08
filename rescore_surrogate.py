#!/usr/bin/env python3
"""
rescore_surrogate.py  -  re-score STORED candidates with a given surrogate.

This is the cheap half of the re-anchor demonstration. The expensive half is
retraining a policy; this half asks the question that actually matters first:

    after adding real Vivado labels from the region the optimiser drove the
    policy into, does the surrogate stop being wrong there?

Nothing is generated and nothing is synthesised -- it walks .sv files already
on disk, predicts Fmax with the supplied checkpoint, and writes one row per
module. analyze_surrogate_error.py --pred then recomputes bias / MAE / Spearman
/ clamp-saturation against the real numbers in ppa.jsonl, so surrogate_v3 and
surrogate_v4 are compared on identical candidates.

    python rescore_surrogate.py --surrogate surrogate_v4.pt --out pred_v4.jsonl
"""

import os
import re
import json
import glob
import argparse

import numpy as np
import torch
import torch.nn as nn

from surrogate_train import extract_features, clamp_fmax

HERE = os.path.dirname(os.path.abspath(__file__))
V8_DIRS = [os.path.join(HERE, "rtl", d) for d in
           ("holdout_eval_v8_firfirr", "holdout_eval_v8_poly",
            "holdout_eval_v8_iirmed")]
LOGF_MIN, LOGF_MAX = float(np.log(5.0)), float(np.log(500.0))


def load_surrogate(path):
    ck = torch.load(path, map_location="cpu")
    nfeat = len(ck["feat_names"])
    net = nn.Sequential(nn.Linear(nfeat, 32), nn.ReLU(),
                        nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))
    net.load_state_dict(ck["state"])
    net.eval()
    mu = torch.tensor(ck["mu"], dtype=torch.float32)
    sd = torch.tensor(ck["sd"], dtype=torch.float32)
    log_target = ck.get("log_target", True)

    @torch.no_grad()
    def predict(rtl):
        x = torch.tensor(extract_features(rtl, ck["feat_names"]),
                         dtype=torch.float32)
        out = net(((x - mu) / sd).unsqueeze(0)).item()
        if log_target:
            out = min(max(out, LOGF_MIN), LOGF_MAX)
            return clamp_fmax(float(np.exp(out)))
        return clamp_fmax(out)
    return predict, ck["feat_names"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surrogate", required=True)
    ap.add_argument("--dirs", nargs="*", default=V8_DIRS)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    predict, feats = load_surrogate(args.surrogate)
    print(f"{args.surrogate}: {len(feats)} features")

    n = 0
    with open(args.out, "w") as fh:
        for d in args.dirs:
            mani_path = os.path.join(d, "fmax_manifest.json")
            mani = json.load(open(mani_path)) if os.path.exists(mani_path) else {}
            for p in sorted(glob.glob(os.path.join(d, "*.sv"))):
                mod = os.path.splitext(os.path.basename(p))[0]
                rtl = open(p, "r", errors="replace").read()
                info = mani.get(mod, {})
                fh.write(json.dumps({
                    "module": mod, "dir": os.path.basename(d),
                    "policy": info.get("policy"), "design": info.get("design"),
                    "count": info.get("count", 1), "regime": info.get("regime"),
                    "pred_fmax": predict(rtl)}) + "\n")
                n += 1
    print(f"{n} candidates re-scored -> {args.out}")


if __name__ == "__main__":
    main()
