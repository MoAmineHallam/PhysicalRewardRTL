#!/usr/bin/env python3
"""
compare_surrogate_lodo.py  -  matched-set LODO comparison of two surrogates.

Why this exists
---------------
The paper wants to say: "selecting a reward model by the standard offline
metric would have chosen the BROKEN one." Supporting that with v3's LODO
Spearman against v4's is not sound, because v4 is trained on a strict superset
of v3's rows -- the 43 re-anchor labels deliberately cover the fast, extreme
region the optimizer reaches. A lower Spearman on the larger set can mean a
harder evaluation set rather than a worse model, and the two numbers are not
computed over the same targets at all.

This script scores both dataset definitions over an IDENTICAL set of target
rows: the intersection of the two row sets, keyed by module id. For each
held-out design d, it trains one model on (v3 rows minus d) and one on
(v4 rows minus d), and both predict the SAME shared rows of d. Any difference
is then attributable to the training rows, which is the thing being claimed.

Normalisation is refit inside every fold, for both arms. Fitting it on all
data -- as surrogate_train.py did until 2026-08-11 -- leaks the held-out
design's feature distribution into its own evaluation, and leaks it hardest for
designs whose features are unlike the rest, i.e. precisely the extreme-Fmax
rows whose ordering the reward depends on.

Usage (needs torch -> GPU server, not the sandbox):
    export PATH=/zeng_gk/Amine/mas/env_mas/bin:$PATH
    python compare_surrogate_lodo.py \
        --a rtl/fmax_probe_v4 rtl/fmax_data rtl/fmax_d2 \
        --b rtl/fmax_probe_v4 rtl/fmax_data rtl/fmax_d2 rtl/fmax_d3 \
        --label-a surrogate_v3 --label-b surrogate_v4 \
        --epochs 4000 --seeds 3 --out surrogate_lodo_cmp.json
"""

import os
import json
import argparse

import numpy as np

from surrogate_train import load_dataset, spearman


def fit_predict(Xtr, ytr, Xte, epochs, seed):
    """Train the surrogate MLP on one fold and predict. Same architecture and
    optimizer as surrogate_train.py, with the fold's own normalisation."""
    import torch
    import torch.nn as nn
    torch.manual_seed(seed)
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xt = torch.tensor((Xtr - mu) / sd, dtype=torch.float32)
    yt = torch.tensor(ytr, dtype=torch.float32).view(-1, 1)
    net = nn.Sequential(nn.Linear(Xtr.shape[1], 32), nn.ReLU(),
                        nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 1))
    opt = torch.optim.Adam(net.parameters(), lr=1e-2)
    for _ in range(epochs):
        opt.zero_grad()
        ((net(Xt) - yt) ** 2).mean().backward()
        opt.step()
    with torch.no_grad():
        return net(torch.tensor((Xte - mu) / sd,
                                dtype=torch.float32)).numpy().ravel()


def pack(rows):
    return {r["key"]: r for r in rows}


def lodo_on_targets(arm_rows, target_mods, epochs, seeds, seed_base=0):
    """LODO predictions for exactly `target_mods`, using arm_rows for training.

    Returns mod -> mean predicted log-Fmax over `seeds` restarts. Every target
    design is fully excluded from its own training fold, including the arm's
    extra rows for that design.
    """
    by_mod = pack(arm_rows)
    designs = sorted({r["design"] for r in arm_rows})
    X = np.array([r["feats"] for r in arm_rows], float)
    y = np.log(np.array([r["fmax"] for r in arm_rows], float))
    dz = np.array([r["design"] for r in arm_rows])
    mods = [r["key"] for r in arm_rows]
    idx = {m: i for i, m in enumerate(mods)}

    out = {}
    for d in designs:
        tgt = [m for m in target_mods
               if m in by_mod and by_mod[m]["design"] == d]
        if not tgt:
            continue
        tr = dz != d
        if tr.sum() < 8:
            continue
        Xte = np.array([X[idx[m]] for m in tgt], float)
        acc = np.zeros(len(tgt))
        for s in range(seed_base, seed_base + seeds):
            acc += fit_predict(X[tr], y[tr], Xte, epochs, s)
        for m, p in zip(tgt, acc / seeds):
            out[m] = float(p)
    return out


def metrics(pred, truth, design_of):
    """Pooled Spearman plus per-design top-1, over the same rows for both arms."""
    mods = sorted(pred)
    p = np.array([pred[m] for m in mods])
    t = np.array([truth[m] for m in mods])
    by = {}
    for m in mods:
        by.setdefault(design_of[m], []).append(m)
    top1 = tot = 0
    for d, ms in by.items():
        if len(ms) < 2:
            continue
        fm = np.array([np.exp(truth[m]) for m in ms])
        if fm.max() - fm.min() < 1:
            continue
        tot += 1
        pv = np.array([pred[m] for m in ms])
        top1 += int(ms[int(np.argmax(pv))] == ms[int(np.argmax(fm))])
    # Errors are reported in MHz after applying the SAME clamp the reward
    # applies, [ln 5, ln 500]. Without it a single fold can dominate: leaving
    # out a design with no near neighbour in the training rows (med3 here) makes
    # the MLP extrapolate to log-Fmax ~3.5e6, and exp() of that overflows to
    # inf, which silently turns mean error and MAE into inf. That blow-up is
    # itself worth knowing about -- it is the same off-support extrapolation the
    # reward clamp exists to contain -- so it is counted rather than hidden.
    LO, HI = np.log(5.0), np.log(500.0)
    n_blow = int((p > HI).sum())
    err = np.exp(np.clip(p, LO, HI)) - np.exp(t)
    return {"n_rows": len(mods), "spearman": float(spearman(p, t)),
            "top1": f"{top1}/{tot}",
            "top1_frac": (top1 / tot) if tot else float("nan"),
            "n_above_clamp": n_blow,
            "max_pred_log": float(p.max()),
            "mean_err_mhz": float(err.mean()),
            "mae_mhz": float(np.abs(err).mean())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", nargs="+", required=True, help="arm A data dirs")
    ap.add_argument("--b", nargs="+", required=True, help="arm B data dirs")
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--epochs", type=int, default=4000)
    ap.add_argument("--seed-base", type=int, default=0,
                    help="offset for the restart seeds. The averaged rho is "
                         "itself a random variable; re-running with a different "
                         "base is how you get an error bar on the v3-vs-v4 gap "
                         "instead of asserting one.")
    ap.add_argument("--seeds", type=int, default=3,
                    help="restarts averaged per fold, to keep the comparison "
                         "from turning on one lucky initialisation")
    ap.add_argument("--out", default="surrogate_lodo_cmp.json")
    args = ap.parse_args()

    rows_a = load_dataset(args.a, exclude_holdout=True)
    rows_b = load_dataset(args.b, exclude_holdout=True)
    a, b = pack(rows_a), pack(rows_b)
    shared = sorted(set(a) & set(b))
    print(f"{args.label_a}: {len(rows_a)} rows, "
          f"{len({r['design'] for r in rows_a})} designs")
    print(f"{args.label_b}: {len(rows_b)} rows, "
          f"{len({r['design'] for r in rows_b})} designs")
    print(f"shared target rows: {len(shared)}")
    if len(shared) < 20:
        raise SystemExit("too few shared rows for a meaningful comparison")
    only_b = sorted(set(b) - set(a))
    print(f"rows only in {args.label_b}: {len(only_b)}"
          + (f"  (e.g. {only_b[0]})" if only_b else ""))

    truth = {m: float(np.log(a[m]["fmax"])) for m in shared}
    design_of = {m: a[m]["design"] for m in shared}

    res = {}
    for label, rows in ((args.label_a, rows_a), (args.label_b, rows_b)):
        print(f"\nLODO for {label} on the shared target rows ...", flush=True)
        pred = lodo_on_targets(rows, shared, args.epochs, args.seeds,
                               args.seed_base)
        common = sorted(set(pred) & set(truth))
        res[label] = metrics({m: pred[m] for m in common},
                             {m: truth[m] for m in common},
                             design_of)
        res[label]["_pred"] = {m: pred[m] for m in common}

    print("\n" + "=" * 72)
    print("MATCHED-SET LODO  (identical target rows, fold-local normalisation)")
    print("=" * 72)
    print(f"{'arm':14s} {'rows':>6s} {'Spearman':>9s} {'top-1':>8s} "
          f"{'mean err':>10s} {'MAE':>8s} {'>clamp':>7s}")
    for label in (args.label_a, args.label_b):
        r = res[label]
        print(f"{label:14s} {r['n_rows']:6d} {r['spearman']:9.3f} "
              f"{r['top1']:>8s} {r['mean_err_mhz']:+9.1f}  {r['mae_mhz']:7.1f} "
              f"{r['n_above_clamp']:7d}")

    A, B = res[args.label_a], res[args.label_b]
    da, db = A["spearman"], B["spearman"]
    # A verdict must not turn on the sign of a difference that is smaller than
    # the noise this estimate carries. MARGIN is deliberately conservative:
    # with ~30 designs, LODO rho moves by more than this between restart seeds.
    MARGIN = 0.03
    votes = {"spearman": da - db,
             "top1": A["top1_frac"] - B["top1_frac"],
             "bias": abs(B["mean_err_mhz"]) - abs(A["mean_err_mhz"])}
    prefers_a = sum(1 for v in votes.values() if v > 0)
    print("\nper-metric preference (positive = prefers "
          f"{args.label_a}): " +
          ", ".join(f"{k} {v:+.3f}" for k, v in votes.items()))
    print()
    if da - db > MARGIN and prefers_a == len(votes):
        print(f"On identical rows the offline metric clearly prefers "
              f"{args.label_a} ({da:.3f} vs {db:.3f}),\nand every metric agrees."
              f" The claim that standard model selection picks the\nreward that "
              f"fails under optimization is SUPPORTED as a controlled result.")
    elif db - da > MARGIN and prefers_a == 0:
        print(f"On identical rows the offline metric clearly prefers "
              f"{args.label_b} ({db:.3f} vs {da:.3f}).\nThe earlier gap was an "
              f"artifact of scoring the two arms on different row sets.\nDO NOT "
              f"claim the offline metric picks the broken model.")
    else:
        print(f"INDISTINGUISHABLE. The gap ({da:.3f} vs {db:.3f}, "
              f"|d|={abs(da-db):.3f}) is below the {MARGIN}\nmargin"
              + ("" if prefers_a in (0, len(votes))
                 else " and the metrics disagree with each other")
              + f". DO NOT claim the offline metric picks the broken\nmodel, "
              f"and do not claim it picks the good one either. The defensible\n"
              f"statement is that no offline metric available at selection time "
              f"separates\nthem, while their behaviour under optimization "
              f"differs enormously -- which\nis a cleaner form of the thesis: "
              f"offline validity does not transfer.")

    json.dump(res, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
