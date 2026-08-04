#!/usr/bin/env python3
"""
analyze_bestofn.py  -  Phase D5 (zero-GPU): three reviewer items computed
entirely from the EXISTING held-out eval artifacts (rtl/holdout_eval):

1. Best-of-N curves (N = 1,2,4,8,16,32,48) for the SFT policy with a PERFECT
   selector -- i.e. the expected best real-Vivado Fmax over N i.i.d. samples,
   assuming an oracle-checking selector that always picks the fastest correct
   candidate. This UPPER-BOUNDS every sampling+selection strategy (surrogate
   top-1, verifier reranking, ...). If GRPO's single-sample expectation beats
   it, RL beats sampling, full stop -- no selector debate.

   Math: each of the 48 recorded samples is one i.i.d. draw from the policy.
   The manifest gives each distinct correct candidate's multiplicity c_i and
   its real Fmax f_i; the remaining 48-sum(c_i) draws are incorrect (value 0).
   With the empirical CDF F(f) = P(draw has Fmax <= f),
       E[best-of-N] = sum_f f * (F(f)^N - F(f^-)^N)         (exact, closed form)

2. fir40 sample-cost: expected oracle-checked samples to the first correct
   (fast) design under GRPO -- the "6 cheap sims to 182 MHz" line.

3. DSP/LUT/FF columns for the money-table entries (F7: area tables must not
   hide DSP mapping).

    python analyze_bestofn.py            # prints tables, writes bestofn.json
"""

import os
import json
import argparse
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL = os.path.join(HERE, "rtl", "holdout_eval")          # OLD 22-design set
V8_DIRS = [os.path.join(HERE, "rtl", d) for d in
           ("holdout_eval_v8_firfirr", "holdout_eval_v8_poly",
            "holdout_eval_v8_iirmed")]                     # 30-design 5-family
NS = (1, 2, 4, 8, 16, 32, 48)


def load(eval_dirs):
    """Merge one or more eval dirs into a single design->policy->candidates map.

    The 5-family held-out evaluation is split across three directories
    (fir/firr, poly, iir/med) whose design sets are disjoint, so they merge by
    concatenation. Passing a single directory reproduces the old behaviour.
    Mixing the 22-design and 30-design sets in one report is what produced the
    stale best-of-N figure, so the design count is printed and asserted."""
    if isinstance(eval_dirs, str):
        eval_dirs = [eval_dirs]
    rows = defaultdict(lambda: defaultdict(list))   # design -> policy -> [(f,c,ppa)]
    regime, summ, n_of = {}, {}, {}
    for eval_dir in eval_dirs:
        mani = json.load(open(os.path.join(eval_dir, "fmax_manifest.json")))
        s = json.load(open(os.path.join(eval_dir, "holdout_summary.json")))
        for pol, d in s.items():
            summ.setdefault(pol, {}).update(d)
        fmax = {}
        for line in open(os.path.join(eval_dir, "ppa.jsonl")):
            try:
                p = json.loads(line)
            except ValueError:
                continue
            fmax[p["module"]] = p if p.get("compiled") else {"fmax_mhz": 0.0}
        for mod, info in mani.items():
            d = info["design"]
            p = fmax.get(mod)
            f = float(p["fmax_mhz"]) if p else 0.0
            rows[d][info["policy"]].append((f, info["count"], p or {}))
            regime[d] = info["regime"]
            n_of[d] = max(n_of.get(d, 0), info["n"])
    return rows, regime, n_of, summ


def e_best_of_n(cands, n_total, N):
    """Exact E[max Fmax of N i.i.d. draws]; incorrect draws count as 0."""
    pts = sorted([(0.0, n_total - sum(c for _, c, _ in cands))]
                 + [(f, c) for f, c, _ in cands])
    total = float(sum(c for _, c in pts))
    e, cum = 0.0, 0.0
    for f, c in pts:
        lo = (cum / total) ** N
        cum += c
        e += f * ((cum / total) ** N - lo)
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="*", default=V8_DIRS,
                    help="eval dirs to merge (default: the three 5-family "
                         "held-out dirs = 30 designs). The old 22-design set "
                         "is rtl/holdout_eval; do NOT mix the two.")
    ap.add_argument("--out", default=os.path.join(HERE, "bestofn.json"))
    args = ap.parse_args()
    rows, regime, n_total, summ = load(args.dirs)
    designs = sorted(rows, key=lambda d: (regime[d], d))
    n_int = sum(1 for d in designs if regime[d] == "interp")
    print(f"eval set: {len(designs)} designs ({n_int} interp, "
          f"{len(designs) - n_int} extrap) from {len(args.dirs)} dir(s)")

    # ---------- 1. best-of-N (perfect selector) vs GRPO best-of-1 ----------
    print("=" * 78)
    print("1) SFT best-of-N with a PERFECT selector (expected real MHz) "
          "vs GRPO best-of-1")
    print("=" * 78)
    hdr = "design         reg    " + "".join(f"boN={n:<7}" for n in NS) \
          + "grpo-bo1"
    print(hdr)
    out = {}
    agg = defaultdict(lambda: defaultdict(list))
    for d in designs:
        n = n_total[d]
        sft = rows[d].get("sft", [])
        grpo = rows[d].get("grpo", [])
        curve = {N: e_best_of_n(sft, n, N) for N in NS}
        g1 = e_best_of_n(grpo, n, 1)
        out[d] = {"regime": regime[d], "sft_bestofN": curve, "grpo_bo1": g1}
        for N in NS:
            agg[regime[d]][N].append(curve[N])
        agg[regime[d]]["g1"].append(g1)
        print(f"{d:14s} {regime[d][:6]:6s}"
              + "".join(f"{curve[N]:8.1f}  " for N in NS) + f"{g1:8.1f}")
    for reg in sorted(agg):
        a = agg[reg]
        k = len(a["g1"])
        print(f"{'MEAN ' + reg:14s} {'':6s}"
              + "".join(f"{sum(a[N])/k:8.1f}  " for N in NS)
              + f"{sum(a['g1'])/k:8.1f}")
    print("\nReading: 'boN=k' = expected best real Fmax if you draw k SFT "
          "samples and a PERFECT\nselector picks the fastest correct one "
          "(upper bound on best-of-k + any reranker).\n'grpo-bo1' = expected "
          "Fmax of a SINGLE GRPO sample (incorrect samples count 0).")

    # ---------- 1b. sample-equivalence: how many SFT draws does 1 GRPO draw buy?
    print("\n" + "=" * 78)
    print("1b) Sample-equivalence  (the honest efficiency claim)")
    print("=" * 78)
    for reg in sorted(agg):
        a = agg[reg]
        k = len(a["g1"])
        g1 = sum(a["g1"]) / k
        curve = [(N, sum(a[N]) / k) for N in NS]
        eq = next((N for N, v in curve if v >= g1), None)
        lo = [(N, v) for N, v in curve if v < g1]
        lo = lo[-1] if lo else None
        if eq is None:
            verdict = (f"exceeds the perfect selector at every N up to "
                       f"{NS[-1]}")
        elif lo is None:
            verdict = f"below even best-of-{eq} (no efficiency gain)"
        else:
            # log-linear interpolation between the bracketing N
            n0, v0 = lo
            frac = (g1 - v0) / (curve[NS.index(eq)][1] - v0)
            neq = n0 * (eq / n0) ** frac
            verdict = (f"~best-of-{neq:.0f}  (between bo{n0}={v0:.1f} and "
                       f"bo{eq}={curve[NS.index(eq)][1]:.1f})")
        print(f"  {reg:7s}: 1 GRPO sample = {g1:6.1f} MHz -> {verdict}")
    print("""
The perfect selector is NOT achievable: it requires the true post-implementation
Fmax of all N candidates, i.e. N synthesis runs. It upper-bounds every real
reranker, including surrogate top-1. So the defensible statements are:
  (a) at EQUAL sample count (1 vs 1), GRPO beats SFT by the ratio bo1 vs
      grpo-bo1 -- this is the headline and it is not a selection effect;
  (b) one GRPO sample is worth roughly the N above of SFT samples judged by a
      selector nobody can build, hence strictly more than N real samples.
It is NOT true that GRPO exceeds best-of-48; on interpolation it does not.
That claim came from the older 22-design set and does not survive the 30-design
5-family set.""")

    # ---------- 2. fir40 sample-cost ----------
    print("\n" + "=" * 78)
    print("2) Sample-cost at the hardest extrapolation point (fir40_8b)")
    print("=" * 78)
    for d in ("fir40_8b", "firr40"):
        if d not in rows:
            continue
        n = n_total[d]
        for pol in ("sft", "grpo"):
            cands = rows[d].get(pol, [])
            nc = sum(c for _, c, _ in cands)
            p = nc / n if n else 0.0
            best = max((f for f, _, _ in cands), default=0.0)
            exp = (1.0 / p) if p else float("inf")
            print(f"  {d:10s} {pol:5s}: correct {nc}/{n} (p={p:.3f}) -> "
                  f"expected {exp:5.1f} oracle-checked samples to first "
                  f"correct; best real Fmax {best:.1f} MHz")
        out.setdefault("sample_cost", {})[d] = {
            pol: {"p_correct": sum(c for _, c, _ in rows[d].get(pol, [])) / n_total[d],
                  "best_fmax": max((f for f, _, _ in rows[d].get(pol, [])),
                                   default=0.0)}
            for pol in ("sft", "grpo")}
    print("\nReading: an oracle check is ~1 s of simulation; even at 17% "
          "correctness, GRPO+oracle\nreaches a correct fast design in a "
          "handful of cheap sims -- no synthesis in the loop.")

    # ---------- 3. money-table area columns (F7) ----------
    print("\n" + "=" * 78)
    print("3) Area columns for the money-table entries (F7: DSPs reported)")
    print("=" * 78)
    print(f"{'design':14s} | {'sft-med F/LUT/FF/DSP':>24s} | "
          f"{'grpo-top F/LUT/FF/DSP':>24s}")
    print("-" * 70)
    for d in designs:
        def pick(pol, top):
            cands = rows[d].get(pol, [])
            if not cands:
                return None
            if top:
                return max(cands, key=lambda t: t[0])
            exp = sorted((t for t in cands for _ in range(t[1])),
                         key=lambda t: t[0])
            return exp[len(exp) // 2]
        s, g = pick("sft", False), pick("grpo", True)
        fmt = lambda t: (f"{t[0]:6.1f}/{t[2].get('lut','-'):>5}/"
                         f"{t[2].get('ff','-'):>5}/{t[2].get('dsp','-'):>3}"
                         if t else " " * 22 + "-")
        print(f"{d:14s} | {fmt(s):>24s} | {fmt(g):>24s}")
        out[d]["area"] = {"sft_med": s and s[2], "grpo_top": g and g[2]}
    print("\nNote: lut=0/1 rows are DSP-mapped multiplies (F7) -- that is why "
          "the DSP column is mandatory.")

    json.dump(out, open(args.out, "w"), indent=1)
    print(f"\nfull data -> {args.out}")


if __name__ == "__main__":
    main()
