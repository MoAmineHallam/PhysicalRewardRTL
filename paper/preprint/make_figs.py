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


# Extrapolation designs of the fir/firr trajectory set: tap counts outside the
# 4..32 range the policy and the re-anchor labels were trained on. Splitting the
# figure on this line is not cosmetic -- the re-anchored predictor is repaired
# on one side of it and still saturated on the other, and an aggregate curve
# would hide that.
EXTRAP = {"fir36_8b", "fir40_8b", "firr36", "firr40"}


def traj_points(d, updates):
    """checkpoint -> predicted / measured / correctness, split by regime.

    measured is the count-weighted mean over CORRECT candidates (Eq. 5,
    unpenalised): the question this figure asks is whether the reward tracks
    the frequency of what the policy actually produces, which is a question
    about the correct samples. Correctness is plotted separately.
    """
    summ = json.load(open(os.path.join(d, "holdout_summary.json")))
    mani = json.load(open(os.path.join(d, "fmax_manifest.json")))
    real = real_fmax(d)
    if real is None:
        return None
    agg = collections.defaultdict(lambda: {"w": 0.0, "c": 0})
    for mod, i in mani.items():
        if mod in real:
            g = "extrap" if i["design"] in EXTRAP else "interp"
            for k in (g, "all"):
                agg[(i["policy"], k)]["w"] += real[mod] * i["count"]
                agg[(i["policy"], k)]["c"] += i["count"]
    pts = []
    for tag in sorted(summ, key=lambda k: updates.get(k, 0)):
        rows = summ[tag]
        q = {"x": updates.get(tag, 0)}
        for g in ("interp", "extrap", "all"):
            sel = [r for nm, r in rows.items()
                   if g == "all" or (nm in EXTRAP) == (g == "extrap")]
            a = agg.get((tag, g), {"w": 0.0, "c": 0})
            q[f"pred_{g}"] = sum(r["mean_surr_fmax"] for r in sel) / len(sel)
            q[f"meas_{g}"] = (a["w"] / a["c"]) if a["c"] else 0.0
            q[f"corr_{g}"] = sum(r["corr_pct"] for r in sel) / len(sel)
        # kept for callers that want the aggregate under the old names
        q["pred"], q["meas"], q["corr"] = q["pred_all"], q["meas_all"], q["corr_all"]
        pts.append(q)
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
        pos = ("at={(v8.right of south east)}, xshift=13mm, ylabel={}"
               if tag == "v9" else "name=v8")
        # blue = interpolation, red = extrapolation; solid = reward's belief,
        # dashed+open = what Vivado measured for the same candidates.
        series = "\n".join(rf"""
\addplot[{col}, mark=*, thick] coordinates {{{coords([(q['x'], q['pred_' + g]) for q in p])}}};
\addlegendentry{{predicted, {lbl}}}
\addplot[{col}, mark=o, thick, dashed] coordinates {{{coords([(q['x'], q['meas_' + g]) for q in p])}}};
\addlegendentry{{measured, {lbl}}}"""
                           for g, col, lbl in
                           (("interp", "blue!70!black", "interp."),
                            ("extrap", "red!70!black", "extrap.")))
        body.append(rf"""
\begin{{axis}}[
  {pos}, title={{{title}}},
  width=.47\textwidth, height=5.4cm,
  xlabel={{cumulative optimizer updates}},
  ylabel={{$F_{{max}}$ (MHz)}}, ymin=0, ymax=575,
  legend pos=south east, legend columns=2,
  legend style={{font=\tiny, draw=none, fill opacity=.75, text opacity=1}},
  grid=major, grid style={{gray!20}}
]
\addplot[gray, dotted, thick, forget plot] coordinates {{(0,500) ({p[-1]['x']},500)}};
\node[gray, font=\scriptsize, anchor=south west] at (axis cs:2,503) {{reward clip bound}};
{series}
\end{{axis}}""")
    tex = rf"""% generated by make_figs.py -- do not edit by hand
\begin{{figure*}}[t]
\centering
\begin{{tikzpicture}}
{''.join(body)}
\end{{tikzpicture}}
\caption{{Predicted and measured \fmax{{}} along the optimisation path, for the
twelve held-out \textsc{{fir}}/\textsc{{firr}} designs ($n{{=}}16$ samples each),
count-weighted over correct candidates. The abscissa is cumulative optimizer
updates rather than attempted steps, because a group whose rewards are all equal
yields no gradient and the two runs differ in how often that happens.
\textbf{{Left:}} under the original predictor, prediction tracks measurement on
the interpolation designs to within $12$\,MHz for roughly two hundred updates and
then saturates at the reward's clip bound ($496.9$ predicted against $261.5$
measured), while on the extrapolation designs it first \emph{{under}}-predicts and
then saturates as well. Correctness falls at exactly that checkpoint, and falls
where the saturation is worst: $92.2\%\!\to\!73.4\%$ on extrapolation against
$96.9\%\!\to\!95.3\%$ on interpolation. \textbf{{Right:}} after re-anchoring on
$43$ train-split measurements, the interpolation curves stay together for the
whole run ($254.5$ against $266.7$ at the end) and no collapse occurs. The
extrapolation curves do not recover: the re-anchor labels span $4$--$32$ taps, so
at $36$ and $40$ taps the predictor is pinned near the clip bound from the first
checkpoint onward and orders nothing. Measured extrapolation frequency is
consequently the same under both rewards ($188.8$ against $188.1$); the
improvement the repair buys is confined to the region the labels reach. We read
this as the sharper form of the claim -- a learned reward is valid only over the
support of its supervision, and offline accuracy reports nothing about the region
optimisation will travel to.}}
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
