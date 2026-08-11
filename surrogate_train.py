#!/usr/bin/env python3
"""
surrogate_train.py  -  Stage 3: train an Fmax surrogate from RTL TEXT (no Vivado).

Why: GRPO needs a reward per sampled candidate, but calling Vivado/the board on
every sample is unaffordable. The surrogate predicts Fmax from the RTL text alone
so GRPO runs at LLM speed; it only needs to RANK candidates of the same design
(GRPO uses relative advantage), and is periodically re-anchored to real Vivado
measurements (supervisor Architecture 1). A 45-pair probe already gave LODO
Spearman 0.64 / top-1 5-of-7 with a trivial linear model; this trains a small MLP
on the full (RTL->Fmax) dataset and reports leave-one-design-out rank metrics.

Data: one or more run_ppa ppa.jsonl files (module, fmax_mhz, compiled) + the
matching fmax_manifest.json (module -> design/family) + the RTL dir(s).

    python surrogate_train.py --data rtl/fmax_probe_v4 rtl/fmax_data --out surrogate.pt
"""

import os
import re
import json
import argparse

import numpy as np

# F2 (surrogate gaming, CONFIRMED): GRPO once drove poly4 to a surrogate Fmax of
# +inf (exp overflow in the MLP head) and firr8 to 441-566 "MHz", far above any
# real Vivado value. The surrogate is only a RANKING signal over a design's
# candidates, and no real design in the training data is below 5 or above 500
# MHz, so predictions outside that band are pure extrapolation artifacts. Clamp
# predicted log-Fmax to [ln 5, ln 500] wherever the surrogate is CONSUMED (GRPO
# reward, eval). This module is the single source of truth for the bound.
FMAX_MIN, FMAX_MAX = 5.0, 500.0
LOGF_MIN, LOGF_MAX = float(np.log(FMAX_MIN)), float(np.log(FMAX_MAX))


def clamp_fmax(fmax):
    """Clamp a predicted Fmax (MHz) to the real training range [5, 500]."""
    if fmax != fmax:                 # NaN -> floor (treat as a non-signal)
        return FMAX_MIN
    return float(min(max(fmax, FMAX_MIN), FMAX_MAX))


# ---- TEXT-ONLY features (must be computable with NO synthesis) --------------
def feature_dict(txt):
    stmts = txt.split(";")
    fd = {}
    fd["max_stmt_mult"] = max((s.count("*") for s in stmts), default=0)
    fd["n_mult"] = txt.count("*")
    fd["n_posedge"] = txt.count("posedge")
    # NOTE kept verbatim for old checkpoints: counts BOTH nonblocking assigns
    # and <= comparisons (conflated; harmless for mult-based families, wrong
    # for comparator networks -- that is what the v3 features below fix).
    fd["n_nonblock"] = txt.count("<=")
    accum = len(re.findall(r"<=[^;]*\*[^;]*\+[^;]*\b[a-z]+\d", txt))
    fd["accum"] = accum
    fd["y_comb"] = 1 if re.search(r"always\s*@\s*\(\s*\*\s*\)[^;]*\by\b",
                                  txt) else 0
    fd["n_lines"] = txt.count("\n")
    fd["n_regs"] = len(set(re.findall(r"\breg\s+(?:\[[^\]]*\]\s*)?(\w+)",
                                      txt)))
    # ratio of multiply-add work that is registered vs lumped combinationally
    fd["pipe_ratio"] = accum / (fd["n_mult"] + 1.0)
    # v3 features (D2): comparator-network families (med) have ZERO multiplies,
    # so their critical path is invisible to the features above.
    fd["n_ternary"] = txt.count("?")                       # mux/compare-swaps
    fd["n_cmp"] = len(re.findall(r"\w\s*(?:<|>)=?\s*[\w(]", txt))  # compares
    fd["nb_assign"] = len(re.findall(r"^\s*\w+(?:\[[^\]]*\])?\s*<=", txt,
                                     re.M))                # TRUE nonblocking
    return fd


def extract_features(txt, feats=None):
    """Feature vector for `txt`, in the order of `feats` (default: the current
    FEAT_NAMES). Consumers scoring an EXISTING checkpoint must pass the
    checkpoint's own feat_names so old nets keep seeing their 9 features."""
    fd = feature_dict(txt)
    return [fd[n] for n in (feats or FEAT_NAMES)]

FEAT_NAMES = ["max_stmt_mult", "n_mult", "n_posedge", "n_nonblock", "accum",
              "y_comb", "n_lines", "n_regs", "pipe_ratio",
              "n_ternary", "n_cmp", "nb_assign"]           # v3 (D2)


def design_of(mod):
    return mod.rsplit("__g", 1)[0]


def base_design(mod, manifest_entry=None):
    """Underlying catalog design name for a labelled module, for the §5 holdout
    check. Prefers the manifest 'design' field (policy_cmp-style manifests tag
    modules like grpo__poly4_8b__g1 with the true design); strips any
    policy-prefix left in the name (a __-joined tag) as a fallback."""
    d = None
    if isinstance(manifest_entry, dict):
        d = manifest_entry.get("design")
    d = d or design_of(mod)
    return d.split("__")[-1]


def load_dataset(dirs, exclude_holdout=True):
    """Labelled (RTL -> Fmax) rows from run_ppa output dirs.

    exclude_holdout (default ON): drop rows whose underlying design is in the
    frozen §5 held-out split -- invariant #3 says held-out designs must never
    appear in the surrogate's training rows. Only disable for debugging."""
    from gen_sft_corpus import is_holdout
    rows, dropped = [], 0
    for d in dirs:
        ppa = os.path.join(d, "ppa.jsonl")
        man = os.path.join(d, "fmax_manifest.json")
        if not (os.path.exists(ppa) and os.path.exists(man)):
            print(f"  [skip] {d}: needs ppa.jsonl + fmax_manifest.json")
            continue
        manifest = json.load(open(man))
        for line in open(ppa):
            try:
                p = json.loads(line)
            except ValueError:
                continue
            mod = p.get("module")
            if not p.get("compiled") or mod not in manifest:
                continue
            if exclude_holdout and is_holdout(base_design(mod, manifest.get(mod))):
                dropped += 1
                continue
            f = os.path.join(d, mod + ".sv")
            if not os.path.exists(f):
                continue
            # `mod` is NOT unique across data dirs -- the same module name
            # recurs in different probe runs with different RTL and different
            # measured Fmax. Anything that keys rows (e.g. the matched-set
            # comparison in compare_surrogate_lodo.py) must use `key`, not
            # `mod`, or it will silently collapse distinct rows together.
            rows.append({"mod": mod, "design": design_of(mod),
                         "key": os.path.join(os.path.basename(d), mod),
                         "src": d,
                         "fmax": float(p.get("fmax_mhz", 0.0)),
                         "feats": extract_features(open(f).read())})
    if dropped:
        print(f"  [holdout] dropped {dropped} labelled rows on §5 held-out "
              f"designs (surrogate training must never see them)")
    return rows


def spearman(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean(); rb -= rb.mean()
    den = np.sqrt((ra**2).sum() * (rb**2).sum())
    return float((ra*rb).sum()/den) if den > 0 else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True,
                    help="dirs each with ppa.jsonl + fmax_manifest.json + *.sv")
    ap.add_argument("--out", default="surrogate.pt")
    ap.add_argument("--epochs", type=int, default=300)
    ap.add_argument("--include-holdout", action="store_true",
                    help="DEBUG ONLY: keep §5 held-out rows (violates the frozen "
                         "isolation protocol; never use for surrogate_v2)")
    args = ap.parse_args()

    if args.include_holdout:
        print("[WARNING] --include-holdout: §5 isolation OFF (debug only)")
    rows = load_dataset(args.data, exclude_holdout=not args.include_holdout)
    if len(rows) < 20:
        raise SystemExit(f"only {len(rows)} labelled pairs; generate more "
                         f"(RTL->Fmax) data before training a surrogate.")
    X = np.array([r["feats"] for r in rows], float)
    y = np.log(np.array([r["fmax"] for r in rows], float))
    dz = np.array([r["design"] for r in rows])
    print(f"dataset: {len(rows)} pairs, {len(set(dz))} designs, "
          f"{X.shape[1]} features")

    import torch
    import torch.nn as nn
    mu, sd = X.mean(0), X.std(0) + 1e-6

    def mlp():
        return nn.Sequential(nn.Linear(X.shape[1], 32), nn.ReLU(),
                             nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))

    # leave-one-design-out evaluation (rank metrics are what GRPO needs).
    # Normalisation is refit INSIDE the fold. Using the all-data mu/sd here --
    # which this script did until 2026-08-11 -- leaks the held-out design's
    # feature distribution into its own evaluation, and does so worst for
    # exactly the designs whose features are unlike the rest, i.e. the
    # extreme-Fmax rows whose ordering the reward depends on.
    preds = np.zeros(len(y))
    for d in sorted(set(dz)):
        tr, te = dz != d, dz == d
        mu_f, sd_f = X[tr].mean(0), X[tr].std(0) + 1e-6
        Xt = torch.tensor((X[tr]-mu_f)/sd_f, dtype=torch.float32)
        yt = torch.tensor(y[tr], dtype=torch.float32).view(-1, 1)
        net = mlp(); opt = torch.optim.Adam(net.parameters(), lr=1e-2)
        for _ in range(args.epochs):
            opt.zero_grad()
            loss = ((net(Xt)-yt)**2).mean(); loss.backward(); opt.step()
        with torch.no_grad():
            preds[te] = net(torch.tensor((X[te]-mu_f)/sd_f,
                            dtype=torch.float32)).numpy().ravel()

    print(f"LODO pooled Spearman(pred, actual) = {spearman(preds, y):.3f}")
    top1 = tot = 0
    for d in set(dz):
        te = np.where(dz == d)[0]
        fm = np.exp(y[te])
        if len(te) < 2 or fm.max()-fm.min() < 1:
            continue
        tot += 1
        top1 += int(te[np.argmax(preds[te])] == te[np.argmax(y[te])])
    print(f"LODO per-design top-1 (picks true fastest): {top1}/{tot}")

    # train final surrogate on ALL data, save with normalisation + feature spec
    Xall = torch.tensor((X-mu)/sd, dtype=torch.float32)
    yall = torch.tensor(y, dtype=torch.float32).view(-1, 1)
    net = mlp(); opt = torch.optim.Adam(net.parameters(), lr=1e-2)
    for _ in range(args.epochs):
        opt.zero_grad(); loss = ((net(Xall)-yall)**2).mean()
        loss.backward(); opt.step()
    torch.save({"state": net.state_dict(), "mu": mu, "sd": sd,
                "feat_names": FEAT_NAMES, "log_target": True}, args.out)
    print(f"surrogate -> {args.out} (predicts log Fmax from RTL text)")


if __name__ == "__main__":
    main()
