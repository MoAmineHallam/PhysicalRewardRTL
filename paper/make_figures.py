#!/usr/bin/env python3
"""
make_figures.py  -  regenerate every figure in the paper from the COMMITTED
measurement artifacts. No numbers are typed by hand: each figure is derived
from the same ppa.jsonl / manifest / summary files the results tables use, so
a figure can never drift from the data that produced it.

Run anywhere with numpy+matplotlib (laptop is convenient because it already has
the Vivado outputs):

    python paper/make_figures.py                 # all figures -> paper/figures/
    python paper/make_figures.py --only money    # one figure
    python paper/make_figures.py --png           # also emit PNG previews

Then commit the PDFs:
    git add paper/figures && git commit -m "paper figures" && git push

Every figure prints the numbers it plotted, so the values can be cross-checked
against RESULTS.md by eye.
"""

import os
import json
import glob
import argparse
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIGS = os.path.join(HERE, "figures")

# grpo_v8 five-family held-out eval, run as three family chunks
V8_DIRS = [os.path.join(ROOT, "rtl", d) for d in
           ("holdout_eval_v8_firfirr", "holdout_eval_v8_poly",
            "holdout_eval_v8_iirmed")]
POLICIES = ["base", "sft", "bestof8", "grpo"]
PRETTY = {"base": "Base", "sft": "SFT", "bestof8": "Best-of-8", "grpo": "GRPO"}
# colour-blind-safe, prints legibly in greyscale (light -> dark by quality)
COLOR = {"base": "#bdbdbd", "sft": "#7fb3d5", "bestof8": "#f0a860",
         "grpo": "#1f4e79"}

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "figure.dpi": 150, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "pdf.fonttype": 42, "ps.fonttype": 42,       # embed TrueType, not Type-3
})


# --------------------------------------------------------------- data loading
def load_eval_dir(d):
    """-> {policy: {design: [(fmax, count), ...]}}, {policy: {design: summary}}.

    Mirrors eval_holdout.report(): a candidate's weight is how many of the n
    samples collapsed onto that distinct implementation, so the per-design mean
    is the expected Fmax of ONE sample from that policy.
    """
    mani_p = os.path.join(d, "fmax_manifest.json")
    ppa_p = os.path.join(d, "ppa.jsonl")
    if not (os.path.exists(mani_p) and os.path.exists(ppa_p)):
        print(f"  [skip] {os.path.basename(d)}: needs fmax_manifest.json + ppa.jsonl")
        return {}, {}
    fmax = {}
    for line in open(ppa_p):
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if p.get("compiled"):
            fmax[p["module"]] = float(p["fmax_mhz"])
    rows = defaultdict(lambda: defaultdict(list))
    for mod, info in json.load(open(mani_p)).items():
        if mod in fmax:
            rows[info["policy"]][info["design"]].append(
                (fmax[mod], info.get("count", 1)))
    sm_p = os.path.join(d, "holdout_summary.json")
    summary = json.load(open(sm_p)) if os.path.exists(sm_p) else {}
    return rows, summary


def load_v8():
    """Merge the three family chunks into one 5-family eval."""
    rows = defaultdict(lambda: defaultdict(list))
    summary = defaultdict(dict)
    for d in V8_DIRS:
        r, s = load_eval_dir(d)
        for pol, dd in r.items():
            for des, cands in dd.items():
                rows[pol][des].extend(cands)
        for pol, dd in s.items():
            summary[pol].update(dd)
    return rows, summary


def weighted_mean(cands, n=48):
    """Freq-weighted mean real Fmax of one sample; non-correct samples score 0."""
    if not cands:
        return 0.0
    return sum(f * c for f, c in cands) / n


def regime_of(summary, design):
    for pol in ("sft", "grpo", "base"):
        if design in summary.get(pol, {}):
            return summary[pol][design].get("regime", "interp")
    return "interp"


def family_of(design):
    for fam in ("firr", "fir", "poly", "iir", "med"):
        if design.startswith(fam):
            return fam
    return "other"


def save(fig, name, png=False):
    os.makedirs(FIGS, exist_ok=True)
    fig.savefig(os.path.join(FIGS, name + ".pdf"))
    if png:
        fig.savefig(os.path.join(FIGS, name + ".png"), dpi=220)
    plt.close(fig)
    print(f"  -> paper/figures/{name}.pdf")


# ------------------------------------------------------------------ figure 1
def fig_money(png=False):
    """Grouped bars: mean real Fmax per policy, per regime (5 families)."""
    rows, summary = load_v8()
    if not rows:
        return
    designs = sorted({d for pol in rows for d in rows[pol]})
    out = {}
    for reg in ("interp", "extrap"):
        ds = [d for d in designs if regime_of(summary, d) == reg]
        out[reg] = {p: float(np.mean([weighted_mean(rows[p].get(d, []))
                                      for d in ds])) for p in POLICIES}
        print(f"  {reg} ({len(ds)} designs): " +
              ", ".join(f"{PRETTY[p]} {out[reg][p]:.1f}" for p in POLICIES))

    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    x = np.arange(2)
    w = 0.2
    for i, p in enumerate(POLICIES):
        v = [out["interp"][p], out["extrap"][p]]
        b = ax.bar(x + (i - 1.5) * w, v, w, label=PRETTY[p], color=COLOR[p],
                   edgecolor="black", linewidth=0.4)
        ax.bar_label(b, fmt="%.0f", fontsize=6, padding=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f"Interpolation\n({sum(1 for d in designs if regime_of(summary,d)=='interp')} designs)",
                        f"Extrapolation\n({sum(1 for d in designs if regime_of(summary,d)=='extrap')} designs)"])
    ax.set_ylabel("Mean $F_{max}$ (MHz), real Vivado")
    ax.set_ylim(0, max(out['interp']['grpo'], out['extrap']['grpo']) * 1.25)
    ax.legend(frameon=False, ncol=2, loc="upper right")
    save(fig, "fig_money", png)


# ------------------------------------------------------------------ figure 2
def fig_mechanism(png=False):
    """THE mechanism figure: per-candidate real Fmax, SFT vs GRPO, per design.

    SFT scatters across a slow cluster with an occasional fast outlier; GRPO
    concentrates on the fast style. Marker area is proportional to how many of
    the 48 samples produced that implementation.
    """
    rows, summary = load_v8()
    if not rows:
        return
    designs = [d for d in sorted({d for d in rows.get("sft", {})},
                                 key=lambda d: (family_of(d), d))
               if rows.get("grpo", {}).get(d)]
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    for i, d in enumerate(designs):
        for pol, off, mk in (("sft", -0.17, "o"), ("grpo", 0.17, "D")):
            for f, c in rows[pol].get(d, []):
                ax.scatter(i + off, f, s=6 + 5.0 * c, marker=mk,
                           facecolor=COLOR[pol], edgecolor="black",
                           linewidth=0.3, alpha=0.85, zorder=3)
    ax.set_xticks(range(len(designs)))
    ax.set_xticklabels(designs, rotation=90)
    ax.set_ylabel("Real $F_{max}$ (MHz)")
    h = [plt.Line2D([], [], marker=m, color="none", markerfacecolor=COLOR[p],
                    markeredgecolor="black", markersize=5, label=PRETTY[p])
         for p, m in (("sft", "o"), ("grpo", "D"))]
    ax.legend(handles=h, frameon=False, ncol=2, loc="upper left")
    ax.set_title("Per-candidate $F_{max}$: SFT samples scatter, GRPO concentrates "
                 "on the fast style (marker area $\\propto$ sample count)",
                 fontsize=7.5)
    save(fig, "fig_mechanism", png)


# ------------------------------------------------------------------ figure 3
def fig_bestofn(png=False):
    """Expected best-of-N under a PERFECT selector vs one GRPO sample."""
    p = os.path.join(ROOT, "rtl", "holdout_eval", "bestofn.json")
    if not os.path.exists(p):
        print("  [skip] bestofn: run analyze_bestofn.py first")
        return
    d = json.load(open(p))
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    for reg, style in (("interp", "-"), ("extrap", "--")):
        ds = [k for k, v in d.items() if v.get("regime") == reg]
        if not ds:
            continue
        Ns = sorted(int(n) for n in d[ds[0]]["sft_bestofN"])
        curve = [float(np.mean([d[k]["sft_bestofN"][str(n)] for k in ds]))
                 for n in Ns]
        g = float(np.mean([d[k]["grpo_bo1"] for k in ds]))
        ax.plot(Ns, curve, style, marker="o", ms=3, color=COLOR["sft"],
                label=f"SFT best-of-$N$ ({reg})")
        ax.axhline(g, ls=style, color=COLOR["grpo"], lw=1.2,
                   label="GRPO, $N=1$ (%s)" % reg)
        print(f"  {reg}: sft bo1 {curve[0]:.1f} -> bo{Ns[-1]} {curve[-1]:.1f}"
              f" | grpo bo1 {g:.1f}")
    ax.set_xscale("log", base=2)
    ax.set_xlabel("$N$ samples drawn from SFT (perfect selector)")
    ax.set_ylabel("Expected $F_{max}$ (MHz)")
    ax.legend(frameon=False, fontsize=6)
    save(fig, "fig_bestofn", png)


# ------------------------------------------------------------------ figure 4
def fig_saturation(png=False):
    """Reward-hacking diagnostic: surrogate saturation vs correctness change."""
    _, summary = load_v8()
    if not summary:
        return
    xs, ys, labs = [], [], []
    for des, g in summary.get("grpo", {}).items():
        s = summary.get("sft", {}).get(des)
        if not s:
            continue
        xs.append(g.get("max_surr_fmax", 0.0))
        ys.append(g["corr_pct"] - s["corr_pct"])
        labs.append(des)
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    pinned = [i for i, v in enumerate(xs) if v >= 499.0]
    ok = [i for i in range(len(xs)) if i not in pinned]
    ax.scatter([xs[i] for i in ok], [ys[i] for i in ok], s=18, marker="o",
               facecolor=COLOR["sft"], edgecolor="black", linewidth=0.3,
               label="surrogate informative", zorder=3)
    ax.scatter([xs[i] for i in pinned], [ys[i] for i in pinned], s=22,
               marker="X", facecolor="#c0392b", edgecolor="black",
               linewidth=0.3, label="surrogate saturated (clamp)", zorder=3)
    for i in pinned:
        if ys[i] < -8:
            ax.annotate(labs[i], (xs[i], ys[i]), fontsize=5.5,
                        xytext=(-2, -7), textcoords="offset points", ha="right")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_xlabel("GRPO surrogate $F_{max}$ (MHz), clamp at 500")
    ax.set_ylabel("Correctness change,\nGRPO $-$ SFT (pp)")
    ax.legend(frameon=False, fontsize=6, loc="lower left")
    if pinned:
        print(f"  saturated designs: {[labs[i] for i in pinned]}")
        print(f"  mean corr change: saturated {np.mean([ys[i] for i in pinned]):+.1f} pp"
              f" | informative {np.mean([ys[i] for i in ok]):+.1f} pp")
    save(fig, "fig_saturation", png)


# ------------------------------------------------------------------ figure 5
def fig_silicon(png=False):
    """Measured on-board Fmax, SFT vs GRPO, canary-attributed."""
    p = os.path.join(ROOT, "rtl", "holdout_silicon", "catalog_fmax.json")
    if not os.path.exists(p):
        print("  [skip] silicon: catalog_fmax.json not found")
        return
    tab = json.load(open(p)).get("table", {})
    pairs = {}
    for k, v in tab.items():
        for pol in ("sft", "grpo"):
            if k.startswith(pol + "_"):
                pairs.setdefault(k[len(pol) + 1:], {})[pol] = v["silicon_fmax"]
    pairs = {k: v for k, v in pairs.items() if "sft" in v and "grpo" in v}
    if not pairs:
        print("  [skip] silicon: no sft/grpo pairs")
        return
    names = list(pairs)
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    x = np.arange(len(names))
    for i, pol in enumerate(("sft", "grpo")):
        v = [pairs[n][pol] for n in names]
        b = ax.bar(x + (i - 0.5) * 0.36, v, 0.36, label=PRETTY[pol],
                   color=COLOR[pol], edgecolor="black", linewidth=0.4)
        ax.bar_label(b, fmt="%.0f", fontsize=6, padding=1)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_ylabel("Measured silicon $F_{max}$ (MHz)")
    ax.legend(frameon=False, ncol=2)
    for n in names:
        print(f"  {n}: sft {pairs[n]['sft']:.1f} -> grpo {pairs[n]['grpo']:.1f}"
              f"  ({pairs[n]['grpo']/max(pairs[n]['sft'],1e-9):.2f}x)")
    save(fig, "fig_silicon", png)


# ------------------------------------------------------------------ figure 6
def fig_distill(png=False):
    """Capability compression: 7B teacher vs 1.5B student, per family.

    Source: probe_competence runs (n=16/design, train-split designs) reported in
    RESULTS.md 1 and 8b. Kept as literals because probe logs are not committed
    artifacts; update here if the probe is re-run.
    """
    fams = ["fir", "firr", "poly", "iir", "med"]
    teacher = [100.0, 100.0, 100.0, 100.0, 89.6]     # sft_v6c 5-family probe
    student = [68.8, 93.8, 93.8, 87.5, 0.0]          # Qwen2.5-Coder-1.5B
    fig, ax = plt.subplots(figsize=(3.4, 2.1))
    x = np.arange(len(fams))
    for i, (lab, v, c) in enumerate((("7B teacher", teacher, COLOR["grpo"]),
                                     ("1.5B student", student, COLOR["bestof8"]))):
        b = ax.bar(x + (i - 0.5) * 0.36, v, 0.36, label=lab, color=c,
                   edgecolor="black", linewidth=0.4)
        ax.bar_label(b, fmt="%.0f", fontsize=6, padding=1)
    ax.set_xticks(x)
    ax.set_xticklabels(fams)
    ax.set_ylabel("Oracle correctness (\\%)")
    ax.set_ylim(0, 118)
    ax.legend(frameon=False, ncol=2, loc="upper center")
    ax.annotate("capability-size frontier", (4, 6), fontsize=6, ha="center",
                color="#c0392b")
    save(fig, "fig_distill", png)


# ------------------------------------------------------------------ figure 7
def fig_area(png=False):
    """Area cost of the fast style: LUT and FF, SFT-median vs GRPO-top."""
    p = os.path.join(ROOT, "rtl", "holdout_eval", "bestofn.json")
    if not os.path.exists(p):
        print("  [skip] area: bestofn.json not found")
        return
    d = json.load(open(p))
    des, lut_s, lut_g, ff_s, ff_g = [], [], [], [], []
    for k, v in sorted(d.items()):
        a = v.get("area", {})
        if "sft_med" in a and "grpo_top" in a:
            des.append(k)
            lut_s.append(a["sft_med"]["lut"]); lut_g.append(a["grpo_top"]["lut"])
            ff_s.append(a["sft_med"]["ff"]);   ff_g.append(a["grpo_top"]["ff"])
    if not des:
        return
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.2))
    x = np.arange(len(des))
    for ax, (s, g, lab) in zip(axes, ((lut_s, lut_g, "LUTs"),
                                      (ff_s, ff_g, "Flip-flops"))):
        ax.bar(x - 0.2, s, 0.4, label="SFT (median sample)", color=COLOR["sft"],
               edgecolor="black", linewidth=0.4)
        ax.bar(x + 0.2, g, 0.4, label="GRPO (top sample)", color=COLOR["grpo"],
               edgecolor="black", linewidth=0.4)
        ax.set_xticks(x); ax.set_xticklabels(des, rotation=90)
        ax.set_ylabel(lab)
    axes[0].legend(frameon=False, fontsize=6)
    save(fig, "fig_area", png)


# ------------------------------------------------------------------ figure 0
def fig_pipeline(png=False):
    """Method schematic: the correctness gate and the train/report boundary."""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(7.0, 2.15))
    ax.set_xlim(0, 100); ax.set_ylim(-1.5, 34.5); ax.axis("off")

    def box(x, y, w, h, text, fc, fs=7.0, tc="black"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6",
                                    facecolor=fc, edgecolor="black", lw=0.7))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color=tc, linespacing=1.35)

    def arrow(x1, y1, x2, y2, style="-|>", ls="-", col="black"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                     mutation_scale=8, lw=0.8, color=col,
                                     linestyle=ls, shrinkA=0, shrinkB=0))

    box(1, 19, 15, 10, "NL spec\n+ interface", "#eeeeee")
    box(19, 19, 15, 10, "Policy $\\pi_\\phi$\n($G$ samples)", COLOR["sft"])
    box(37, 19, 16, 10, "I/O-equivalence\nORACLE", "#f6d5d2")
    box(56, 25.5, 18, 8, "correct: reward\n$=$ surrogate $F_{max}$", "#d5ecd5", 6.6)
    box(56, 15, 18, 8, "incorrect:\nreward $= 0$", "#f2c9c4", 6.6)
    box(78, 19, 20, 10, "group-normalised\nadvantage; KL to\nfrozen SFT", COLOR["grpo"],
        6.6, "white")

    arrow(16, 24, 19, 24); arrow(34, 24, 37, 24)
    arrow(53, 26, 56, 29); arrow(53, 22, 56, 19)
    arrow(74, 29, 78, 26); arrow(74, 19, 78, 22)
    # feedback to policy
    arrow(88, 19, 88, 11); arrow(88, 11, 26.5, 11); arrow(26.5, 11, 26.5, 19)
    ax.text(57, 12.2, "policy update", fontsize=6.2, ha="center", style="italic")

    # the reporting boundary
    ax.plot([1, 99], [7.2, 7.2], ls=(0, (4, 3)), color="#c0392b", lw=0.9)
    ax.text(2, 8.0, "training loop (surrogate values never leave)",
            fontsize=6.2, color="#c0392b", va="bottom")
    box(24, 0.4, 24, 6, "real Vivado\ntiming closure", "#ffffff", 6.6)
    box(52, 0.4, 24, 6, "measured silicon\n(clock sweep)", "#ffffff", 6.6)
    ax.text(2, 3.2, "reported:", fontsize=6.6, va="center", style="italic")
    save(fig, "fig_pipeline", png)


FIGURES = {"pipeline": fig_pipeline, "money": fig_money, "mechanism": fig_mechanism,
           "bestofn": fig_bestofn, "saturation": fig_saturation,
           "silicon": fig_silicon, "distill": fig_distill, "area": fig_area}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma list: " + ",".join(FIGURES))
    ap.add_argument("--png", action="store_true", help="also write PNG previews")
    args = ap.parse_args()
    want = args.only.split(",") if args.only else list(FIGURES)
    os.makedirs(FIGS, exist_ok=True)
    for name in want:
        fn = FIGURES.get(name.strip())
        if fn is None:
            print(f"[?] unknown figure '{name}' (have: {', '.join(FIGURES)})")
            continue
        print(f"[{name}]")
        try:
            fn(args.png)
        except Exception as e:
            print(f"  [FAIL] {type(e).__name__}: {e}")
    print(f"\nfigures -> {FIGS}\nnext: git add paper/figures && git commit && git push")


if __name__ == "__main__":
    main()
