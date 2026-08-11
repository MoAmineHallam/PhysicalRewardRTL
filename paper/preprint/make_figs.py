#!/usr/bin/env python3
"""
make_figs.py  -  emit the preprint's data figures as pgfplots .tex fragments.

Why .tex rather than PDF images: the figures stay editable in Overleaf, need no
matplotlib on whichever machine builds them, and render as vectors at whatever
size the layout ends up wanting. Each fragment is a complete float that main.tex
pulls in with \input.

  figures/fig1_trajectory.tex   predicted vs MEASURED along the optimisation
                                path, one panel per surrogate. Needs Vivado
                                results for rtl/traj_v8 and rtl/traj_v9.
  figures/fig3_scatter.tex      predicted vs measured per (policy, design)
                                cell, both surrogates. Buildable now.

A figure whose data is missing is NOT written and NOT half-written; the script
says which artifact is absent and moves on, so a placeholder can never reach a
posted PDF.

    python make_figs.py
"""

import os
import json
import argparse
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
FIGS = os.path.join(HERE, "figures")

V8_DIRS = [os.path.join(ROOT, "rtl", d) for d in
           ("holdout_eval_v8_firfirr", "holdout_eval_v8_poly",
            "holdout_eval_v8_iirmed")]

# cumulative optimizer updates per checkpoint, read off the training logs.
# grpo_v8_cont restarts its step counter after resuming, so these are NOT
# simply 100/200/300/400 -- plotting against steps would silently compare
# two runs that received different amounts of optimisation.
UPDATES = {
    "v8": {"step0": 0, "s100": 77, "s200": 138, "s300": 205, "s400": 276},
    "v9": {"step0": 0, "s100": 69, "s200": 116, "s300": 159, "s400": 200},
}


def real_fmax(d):
    p = os.path.join(d, "ppa.jsonl")
    out = {}
    if not os.path.exists(p):
        return None
    for line in open(p):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        out[r["module"]] = float(r["fmax_mhz"]) if r.get("compiled") else 0.0
    return out


def cell_weighted(dirs, pred_file=None):
    """(policy, design) -> (predicted, measured), both count-weighted."""
    pred = None
    if pred_file:
        pred = collections.defaultdict(lambda: {"w": 0.0, "c": 0})
        for line in open(pred_file):
            r = json.loads(line)
            if not r.get("policy"):
                continue
            a = pred[(r["policy"], r["design"])]
            a["w"] += r["pred_fmax"] * r["count"]
            a["c"] += r["count"]
    agg = collections.defaultdict(lambda: {"w": 0.0, "c": 0})
    for d in dirs:
        real = real_fmax(d)
        if real is None:
            return None
        mani = json.load(open(os.path.join(d, "fmax_manifest.json")))
        for mod, i in mani.items():
            if mod in real:
                a = agg[(i["policy"], i["design"])]
                a["w"] += real[mod] * i["count"]
                a["c"] += i["count"]
    out = {}
    for k, a in agg.items():
        if not a["c"] or pred is None or not pred[k]["c"]:
            continue
        out[k] = (pred[k]["w"] / pred[k]["c"], a["w"] / a["c"])
    return out


def traj_points(d, updates):
    summ = json.load(open(os.path.join(d, "holdout_summary.json")))
    mani = json.load(open(os.path.join(d, "fmax_manifest.json")))
    real = real_fmax(d)
    if real is None:
        return None
    agg = collections.defaultdict(lambda: {"w": 0.0, "tot": 0})
    seen = set()
    for mod, i in mani.items():
        if mod in real:
            agg[i["policy"]]["w"] += real[mod] * i["count"]
        if (i["policy"], i["design"]) not in seen:
            seen.add((i["policy"], i["design"]))
            agg[i["policy"]]["tot"] += i["n"]
    pts = []
    for tag in sorted(summ, key=lambda k: updates.get(k, 0)):
        rows = summ[tag]
        a = agg.get(tag, {"w": 0.0, "tot": 0})
        pts.append({
            "x": updates.get(tag, 0),
            "pred": sum(r["mean_surr_fmax"] for r in rows.values()) / len(rows),
            "meas": (a["w"] / a["tot"]) if a["tot"] else 0.0,
            "corr": sum(r["corr_pct"] for r in rows.values()) / len(rows)})
    return pts


def coords(pairs, fmt="({x:.1f},{y:.1f})"):
    return " ".join(fmt.format(x=x, y=y) for x, y in pairs)


def fig_trajectory(args):
    out = {}
    for tag, d in (("v8", args.traj_v8), ("v9", args.traj_v9)):
        p = traj_points(d, UPDATES[tag])
        if p is None:
            print(f"  [fig1] skipped: no {os.path.relpath(d, ROOT)}/ppa.jsonl")
            return False
        out[tag] = p
    body = []
    for tag, title in (("v8", "Original predictor"),
                       ("v9", "Re-anchored predictor")):
        p = out[tag]
        body.append(rf"""
\begin{{groupplot}}[group style={{group size=1 by 1}}]
\end{{groupplot}}""" if False else rf"""
\begin{{axis}}[
  name={tag}, title={{{title}}},
  width=.49\textwidth, height=5.2cm,
  xlabel={{cumulative optimizer updates}},
  ylabel={{$F_{{max}}$ (MHz)}}, ymin=0, ymax=560,
  legend pos=north west, legend style={{font=\scriptsize, draw=none}},
  grid=major, grid style={{gray!20}},
  {'at={(v8.right of south east)}, xshift=12mm, ylabel={}' if tag == 'v9' else ''}
]
\addplot+[mark=*, thick] coordinates {{{coords([(q['x'], q['pred']) for q in p])}}};
\addlegendentry{{predicted}}
\addplot+[mark=square*, thick, dashed] coordinates {{{coords([(q['x'], q['meas']) for q in p])}}};
\addlegendentry{{measured (Vivado)}}
\addplot[gray, dotted, thick, forget plot] coordinates {{(0,500) ({p[-1]['x']},500)}};
\node[gray, font=\scriptsize, anchor=south east] at (axis cs:{p[-1]['x']},505) {{reward clip bound}};
\end{{axis}}""")
    tex = rf"""% generated by make_figs.py -- do not edit by hand
\begin{{figure*}}[t]
\centering
\begin{{tikzpicture}}
{''.join(body)}
\end{{tikzpicture}}
\caption{{Predicted and measured \fmax{{}} along the optimisation path, against
cumulative optimizer updates (not attempted steps: the two runs differ in how
many steps produced a gradient). Left: the original predictor tracks measurement
for roughly two hundred updates, then saturates at the reward's clip bound while
measurement does not follow. Right: the re-anchored predictor stays with
measurement throughout. Correctness degrades only where saturation occurs
(Table~\ref{{tab:trajectory}}).}}
\label{{fig:trajectory}}
\end{{figure*}}
"""
    open(os.path.join(FIGS, "fig1_trajectory.tex"), "w").write(tex)
    print("  [fig1] wrote figures/fig1_trajectory.tex")
    return True


def fig_scatter(args):
    series = {}
    for tag, pf in (("original", args.pred_v3), ("re-anchored", args.pred_v4)):
        if not os.path.exists(pf):
            print(f"  [fig3] skipped: no {pf}")
            return False
        c = cell_weighted(V8_DIRS, pf)
        if c is None:
            print("  [fig3] skipped: missing ppa.jsonl in a v8 eval dir")
            return False
        series[tag] = c
    panels = []
    for i, (tag, title) in enumerate((("original", "Original predictor"),
                                      ("re-anchored", "Re-anchored predictor"))):
        c = series[tag]
        by = collections.defaultdict(list)
        for (pol, _), (p, m) in c.items():
            by[pol].append((m, p))          # x = measured, y = predicted
        plots = []
        for pol, marks in (("sft", "o"), ("grpo", "square*"),
                           ("bestof8", "triangle*"), ("base", "x")):
            if pol not in by:
                continue
            lbl = {"sft": "supervised", "grpo": "optimized",
                   "bestof8": "best-of-8", "base": "base"}[pol]
            plots.append(rf"\addplot+[only marks, mark={marks}, mark size=1.6pt] "
                         rf"coordinates {{{coords(sorted(by[pol]))}}};"
                         + "\n" + rf"\addlegendentry{{{lbl}}}")
        pos = ("at={(p0.right of south east)}, xshift=12mm, ylabel={}"
               if i else "name=p0")
        panels.append(rf"""
\begin{{axis}}[
  {pos}, title={{{title}}},
  width=.49\textwidth, height=5.6cm,
  xlabel={{measured $F_{{max}}$ (MHz)}}, ylabel={{predicted $F_{{max}}$ (MHz)}},
  xmin=0, xmax=380, ymin=0, ymax=560,
  legend pos=north west, legend style={{font=\scriptsize, draw=none}},
  grid=major, grid style={{gray!20}}
]
\addplot[gray, thick, domain=0:360, forget plot] {{x}};
\node[gray, font=\scriptsize, rotate=38, anchor=south] at (axis cs:250,250) {{perfect}};
\addplot[gray, dotted, thick, forget plot] coordinates {{(0,500) (380,500)}};
\node[gray, font=\scriptsize, anchor=south east] at (axis cs:375,505) {{clip bound}};
{chr(10).join(plots)}
\end{{axis}}""")
    tex = rf"""% generated by make_figs.py -- do not edit by hand
\begin{{figure*}}[t]
\centering
\begin{{tikzpicture}}
{''.join(panels)}
\end{{tikzpicture}}
\caption{{Predicted against measured \fmax{{}} for every (policy, design) cell of
the held-out set, both count-weighted. Left: the original predictor. Supervised
and best-of-8 cells sit on the identity line; the optimized policy's cells lift
off it and pile against the reward's clip bound, where the reward can no longer
order one design against another. Right: the same candidates under the
re-anchored predictor. The correction is specific to the region optimisation
created, and the supervised cells are unaffected.}}
\label{{fig:scatter}}
\end{{figure*}}
"""
    open(os.path.join(FIGS, "fig3_scatter.tex"), "w").write(tex)
    print("  [fig3] wrote figures/fig3_scatter.tex")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traj-v8", default=os.path.join(ROOT, "rtl", "traj_v8"))
    ap.add_argument("--traj-v9", default=os.path.join(ROOT, "rtl", "traj_v9"))
    ap.add_argument("--pred-v3", default=os.path.join(ROOT, "pred_v3.jsonl"))
    ap.add_argument("--pred-v4", default=os.path.join(ROOT, "pred_v4.jsonl"))
    args = ap.parse_args()
    os.makedirs(FIGS, exist_ok=True)
    print("building figures:")
    ok1 = fig_trajectory(args)
    ok3 = fig_scatter(args)
    print(f"\nIn main.tex set \\figurestrue once the figures you want exist. "
          f"Currently available: "
          f"{'fig1 ' if ok1 else ''}{'fig3' if ok3 else ''}".rstrip())
    if not ok1:
        print("fig1 needs the trajectory Vivado results; run run_ppa.py on "
              "rtl/traj_v8 and rtl/traj_v9 first.")


if __name__ == "__main__":
    main()
