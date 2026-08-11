#!/usr/bin/env python3
"""
make_figs.py  -  build the preprint's figures from committed artifacts.

Figure 1 is the paper's hero: predicted and MEASURED Fmax along the
optimisation path, one panel per surrogate. It needs the Vivado results for the
trajectory candidate sets:

    rtl/traj_v8/ppa.jsonl     (original surrogate -- the diverging curve)
    rtl/traj_v9/ppa.jsonl     (re-anchored       -- the tracking curve)

Until those exist the script prints exactly what is missing and exits without
writing anything, so a half-built figure can never silently reach the document.
Set \figurestrue in main.tex once figures/ is populated.

    python make_figs.py
"""

import os
import re
import json
import argparse
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FIGS = os.path.join(HERE, "figures")

# checkpoint label -> cumulative optimizer updates (from the training logs;
# grpo_v8_cont restarts its step counter, so these are NOT 100/200/300/400)
UPDATES_V8 = {"step0": 0, "s100": 77, "s200": 138, "s300": 205, "s400": 276}
UPDATES_V9 = {"step0": 0, "s100": 69, "s200": 116, "s300": 159, "s400": 200}


def load_traj(d):
    """Per-checkpoint predicted and measured Fmax, both count-weighted."""
    summ = json.load(open(os.path.join(d, "holdout_summary.json")))
    mani = json.load(open(os.path.join(d, "fmax_manifest.json")))
    ppa = os.path.join(d, "ppa.jsonl")
    real = {}
    if os.path.exists(ppa):
        for line in open(ppa):
            try:
                p = json.loads(line)
            except ValueError:
                continue
            real[p["module"]] = (float(p["fmax_mhz"])
                                 if p.get("compiled") else 0.0)
    agg = collections.defaultdict(lambda: {"w": 0.0, "tot": 0})
    seen = set()
    for mod, i in mani.items():
        k = i["policy"]
        if mod in real:
            agg[k]["w"] += real[mod] * i["count"]
        if (i["policy"], i["design"]) not in seen:
            seen.add((i["policy"], i["design"]))
            agg[k]["tot"] += i["n"]
    out = {}
    for tag, rows in summ.items():
        corr = sum(r["corr_pct"] for r in rows.values()) / len(rows)
        pred = sum(r["mean_surr_fmax"] for r in rows.values()) / len(rows)
        a = agg.get(tag)
        meas = (a["w"] / a["tot"]) if (a and a["tot"] and real) else None
        out[tag] = {"corr": corr, "pred": pred, "measured": meas}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traj-v8", default=os.path.join(ROOT, "rtl", "traj_v8"))
    ap.add_argument("--traj-v9", default=os.path.join(ROOT, "rtl", "traj_v9"))
    args = ap.parse_args()

    missing = [d for d in (args.traj_v8, args.traj_v9)
               if not os.path.exists(os.path.join(d, "ppa.jsonl"))]
    if missing:
        print("Cannot build Figure 1 -- no Vivado results yet for:")
        for d in missing:
            print(f"  {d}/ppa.jsonl")
        print("\nRun on the laptop:")
        for d in missing:
            rel = os.path.relpath(d, ROOT)
            print(f"  python run_ppa.py --dir {rel} --out {rel}/ppa.jsonl "
                  f"--clk clk --period 5.0 --vivado <vivado.bat>")
        print("\nNothing written. Leave \\figuresfalse in main.tex.")
        return

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available here; run this where it is installed "
              "(the numbers below are the figure's content).")
        for d, lab in ((args.traj_v8, "original"), (args.traj_v9, "re-anchored")):
            print(f"\n{lab}:")
            for tag, v in load_traj(d).items():
                print(f"  {tag:6s} corr={v['corr']:5.1f}%  pred={v['pred']:7.1f}"
                      f"  measured={v['measured']:7.1f}")
        return

    os.makedirs(FIGS, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, (d, lab, upd) in zip(axes, (
            (args.traj_v8, "Original predictor", UPDATES_V8),
            (args.traj_v9, "Re-anchored predictor", UPDATES_V9))):
        t = load_traj(d)
        order = sorted(t, key=lambda k: upd.get(k, 0))
        xs = [upd.get(k, 0) for k in order]
        ax.plot(xs, [t[k]["pred"] for k in order], "o-", lw=2,
                label="predicted")
        ax.plot(xs, [t[k]["measured"] for k in order], "s--", lw=2,
                label="measured (Vivado)")
        ax.axhline(500, ls=":", lw=1, color="0.5")
        ax.text(xs[-1], 505, "reward clip bound", ha="right", va="bottom",
                fontsize=8, color="0.4")
        ax2 = ax.twinx()
        ax2.plot(xs, [t[k]["corr"] for k in order], "^-", lw=1, color="0.55",
                 alpha=.8, label="correctness")
        ax2.set_ylim(60, 100)
        ax2.set_ylabel("correctness (%)" if lab.startswith("Re") else "")
        if not lab.startswith("Re"):
            ax2.set_yticklabels([])
        ax.set_title(lab)
        ax.set_xlabel("cumulative optimizer updates")
        ax.grid(alpha=.3)
    axes[0].set_ylabel(r"$F_{max}$ (MHz)")
    axes[0].legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    out = os.path.join(FIGS, "fig1_trajectory.pdf")
    fig.savefig(out)
    print(f"wrote {out}\nNow set \\figurestrue in main.tex.")


if __name__ == "__main__":
    main()
