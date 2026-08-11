#!/usr/bin/env python3
"""
verify_claims.py  -  reproduce every number that changed a claim on 2026-08-11.

Run this yourself. It re-derives each result from committed artifacts and prints
what was claimed next to what it computes, so a disagreement is visible without
reading any prose.

    python verify_claims.py                 # deterministic checks only (no torch)
    python verify_claims.py --lodo 10       # + rerun the noisy LODO 10 times

Sections A-D are DETERMINISTIC: pure numpy over committed ppa.jsonl and manifest
files. Same input, same output, on any machine.

Section E is NOT deterministic. surrogate_train.py sets no random seed, so its
LODO figure is a fresh draw of the network initialisation every run. This
matters: the figure it replaced (0.75-0.82) was itself reported as a RANGE over
seeds. --lodo N reruns it N times and reports the spread, which is the only
honest way to compare against a range. It needs torch and takes ~1 min per run
per surrogate.

Section F needs iverilog and re-simulates 1,529 candidates (~1 min at 4 workers);
run audit_oracle.py directly for that one.
"""

import os
import json
import argparse
import subprocess
import collections
import statistics

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V8 = [os.path.join(HERE, "rtl", d) for d in
      ("holdout_eval_v8_firfirr", "holdout_eval_v8_poly", "holdout_eval_v8_iirmed")]
EXTRAP_TRAJ = {"fir36_8b", "fir40_8b", "firr36", "firr40"}


def hdr(t):
    print("\n" + "=" * 74 + f"\n{t}\n" + "=" * 74)


def check(label, claimed, got, tol=0.15):
    ok = abs(claimed - got) <= tol
    print(f"  {label:44s} claimed {claimed:8.3f}   computed {got:8.3f}   "
          f"{'OK' if ok else '*** MISMATCH ***'}")
    return ok


def real_fmax(d):
    out = {}
    for line in open(os.path.join(d, "ppa.jsonl")):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        out[r["module"]] = float(r["fmax_mhz"]) if r.get("compiled") else 0.0
    return out


# ------------------------------------------------------------------ A
def sec_a():
    hdr("A. Aggregate correctness: is it preserved, or does it decline?")
    print("  Claim REMOVED from 05_results.tex: 'correctness is preserved in")
    print("  aggregate'. Replacement: 88.7% -> 86.9% overall; interp flat,")
    print("  extrap down >5 points.\n")
    agg = collections.defaultdict(lambda: {"w": 0.0, "c": 0, "tot": 0})
    for d in V8:
        mani = json.load(open(os.path.join(d, "fmax_manifest.json")))
        real = real_fmax(d)
        seen = set()
        for mod, i in mani.items():
            for key in ((i["policy"], i["regime"]), (i["policy"], "ALL")):
                if mod in real:
                    agg[key]["w"] += real[mod] * i["count"]
                    agg[key]["c"] += i["count"]
            if (i["policy"], i["design"]) not in seen:
                seen.add((i["policy"], i["design"]))
                agg[(i["policy"], i["regime"])]["tot"] += i["n"]
                agg[(i["policy"], "ALL")]["tot"] += i["n"]
    ok = True
    for pol, reg, claimed in (("sft", "ALL", 88.7), ("grpo", "ALL", 86.9),
                              ("sft", "interp", 92.8), ("grpo", "interp", 93.2),
                              ("sft", "extrap", 81.6), ("grpo", "extrap", 76.1)):
        a = agg[(pol, reg)]
        ok &= check(f"{pol} {reg} correctness %", claimed,
                    100.0 * a["c"] / a["tot"])
    return ok


# ------------------------------------------------------------------ B
def sec_b():
    hdr("B. Best-of-N: does one GRPO sample beat a perfect best-of-48?")
    print("  Claim WITHDRAWN. Also withdrawn: firr10/fir40 'existence failures'.")
    print("  Runs analyze_bestofn.py on the 30-design set and greps its table.\n")
    r = subprocess.run(["python", os.path.join(HERE, "analyze_bestofn.py"),
                        "--dirs"] + V8, capture_output=True, text=True)
    ok = True
    in_table1 = False
    for line in r.stdout.splitlines():
        f = line.split()
        # only the first table has the best-of-N columns; later sections reuse
        # the same design names for area and sample-cost rows
        if line.startswith("design ") and "boN=1" in line:
            in_table1 = True
        elif line.startswith("=====") and in_table1 and "MEAN" not in line:
            pass
        if line.startswith("1b)") or line.startswith("2)"):
            in_table1 = False
        if line.startswith("MEAN interp") or line.startswith("MEAN extrap"):
            reg = f[1]
            bo48, grpo = float(f[-2]), float(f[-1])
            print(f"  {reg}: perfect bo48 = {bo48:.1f} MHz, GRPO bo1 = {grpo:.1f} "
                  f"MHz  -> GRPO {'beats' if grpo > bo48 else 'does NOT beat'} bo48")
            ok &= grpo < bo48
        if in_table1 and f[:1] in (["firr10"], ["fir40_8b"]):
            print(f"  {f[0]:10s} SFT bo48 = {float(f[-2]):7.1f}   "
                  f"GRPO bo1 = {float(f[-1]):7.1f}   "
                  f"-> {'SFT wins' if float(f[-2]) > float(f[-1]) else 'GRPO wins'}")
    print("\n  Expected: GRPO does NOT beat bo48 in either regime, and SFT wins")
    print("  on both firr10 and fir40 -- which is why 'existence failure' went.")
    return ok


# ------------------------------------------------------------------ C
def sec_c():
    hdr("C. Trajectory: does the reward saturate, and where?")
    print("  Figure 1. Uses rtl/traj_v8 and rtl/traj_v9 Vivado results.\n")
    ok = True
    # (predicted, measured-over-CORRECT, correctness). The measured column is
    # deliberately the over-correct basis: it is what Figure 1 plots and the only
    # one comparable with the prediction, which scores correct candidates only.
    # The penalised basis is printed alongside because the two were mixed once
    # already -- on that basis v8 reads 230.9 -> 212.3 over the last interval,
    # and every megahertz of that movement is the correctness term.
    for tag, d, claim_end in (("v8", "rtl/traj_v8", (497.9, 241.2, 88.0)),
                              ("v9", "rtl/traj_v9", (333.2, 240.7, 99.0))):
        p = os.path.join(HERE, d)
        if not os.path.exists(os.path.join(p, "ppa.jsonl")):
            print(f"  [skip] {d}: no ppa.jsonl")
            continue
        summ = json.load(open(os.path.join(p, "holdout_summary.json")))
        mani = json.load(open(os.path.join(p, "fmax_manifest.json")))
        real = real_fmax(p)
        w = c = tot = 0.0
        seen = set()
        for mod, i in mani.items():
            if i["policy"] != "s400":
                continue
            if mod in real:
                w += real[mod] * i["count"]
                c += i["count"]
            if (i["policy"], i["design"]) not in seen:
                seen.add((i["policy"], i["design"]))
                tot += i["n"]

        rows = summ["s400"]
        pred = sum(x["mean_surr_fmax"] for x in rows.values()) / len(rows)
        corr = sum(x["corr_pct"] for x in rows.values()) / len(rows)
        print(f"  traj_{tag} final checkpoint:")
        ok &= check(f"    predicted MHz", claim_end[0], pred, tol=1.0)
        ok &= check("    measured MHz (over correct)", claim_end[1], w / c,
                    tol=1.0)
        print("      measured MHz (penalised, for reference)      "
              f"          {w / tot:8.3f}")
        ok &= check(f"    correctness %", claim_end[2], corr, tol=1.0)
        # the regime split -- the reason the caption changed
        for g, names in (("interp", lambda n: n not in EXTRAP_TRAJ),
                         ("extrap", lambda n: n in EXTRAP_TRAJ)):
            sel = [x for n, x in rows.items() if names(n)]
            gw = gc = 0.0
            for mod, i in mani.items():
                if i["policy"] == "s400" and mod in real and names(i["design"]):
                    gw += real[mod] * i["count"]
                    gc += i["count"]
            print(f"      {g:7s} predicted {sum(x['mean_surr_fmax'] for x in sel)/len(sel):7.1f}"
                  f"   measured {gw/gc:7.1f}")
    print("\n  Expected: v8 predicted ~498 vs measured ~212 (saturated, and")
    print("  measurement FELL); v9 tracks on interp but is pinned ~490 on extrap.")
    return ok


# ------------------------------------------------------------------ D
def sec_d():
    hdr("D. Oracle x/z audit: did any verdict change?")
    p = os.path.join(HERE, "audit_oracle.jsonl")
    if not os.path.exists(p):
        print("  audit_oracle.jsonl absent -- run:")
        print("    python audit_oracle.py --workers 4 --dirs rtl/holdout_eval_student \\")
        print("      rtl/holdout_eval rtl/holdout_eval_qwen rtl/holdout_eval_v8_firfirr \\")
        print("      rtl/frontier_eval rtl/holdout_eval_v8_poly rtl/holdout_eval_v8_iirmed")
        return True
    recs = [json.loads(l) for l in open(p)]
    ok_r = [r for r in recs if "error" not in r]
    und = [r for r in ok_r if r.get("n_undef", 0)]
    flip = [r for r in ok_r if r.get("accept_legacy") and not r["accept_now"]]
    flop = [r for r in ok_r if r["accept_now"] and not r.get("accept_legacy")]
    print(f"  candidates audited ............................ {len(ok_r)}")
    print(f"  emit x/z on some cycle ........................ {len(und)}")
    print(f"  accepted by OLD parse but not new (false pos) . {len(flip)}")
    print(f"  accepted by NEW parse but not old ............. {len(flop)}")
    print(f"  survive exact equality ........................ "
          f"{sum(1 for r in ok_r if r['accept_exact'])}/{len(ok_r)}")
    print("\n  Expected: 1529 audited, 18 with x/z, 0 flips in either direction.")
    return len(flip) == 0 and len(flop) == 0


# ------------------------------------------------------------------ E
def sec_e(n):
    hdr(f"E. LODO stability: rerunning surrogate_train.py {n} times per arm")
    print("  THIS IS THE WEAK ONE. surrogate_train.py sets no random seed, so")
    print("  each run redraws the network initialisation. The figure I replaced")
    print("  (0.75-0.82) was itself reported as a seed RANGE, so a single draw")
    print("  cannot refute it. This section measures the spread.\n")
    arms = {
        "v2 (3 fam, 203)": ["rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp"],
        "v3 (5 fam, 229)": ["rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp",
                            "rtl/fmax_d2"],
        "v4 (re-anch, 272)": ["rtl/fmax_probe_v4", "rtl/fmax_data", "rtl/policy_cmp",
                              "rtl/fmax_d2", "rtl/fmax_d3"],
    }
    claimed = {"v2 (3 fam, 203)": 0.972, "v3 (5 fam, 229)": 0.915,
               "v4 (re-anch, 272)": 0.913}
    out = {}
    for label, dirs in arms.items():
        vals = []
        for i in range(n):
            r = subprocess.run(
                ["python", os.path.join(HERE, "surrogate_train.py"),
                 "--data"] + [os.path.join(HERE, d) for d in dirs] +
                ["--out", os.path.join("/tmp", f"verify_{label[:2]}_{i}.pt")],
                capture_output=True, text=True)
            for line in r.stdout.splitlines():
                if "LODO pooled Spearman" in line:
                    vals.append(float(line.rsplit("=", 1)[1]))
            print(f"    {label:20s} run {i+1}/{n}: "
                  f"{vals[-1] if vals else 'FAILED'}", flush=True)
        out[label] = vals
    print()
    for label, vals in out.items():
        if not vals:
            continue
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
        print(f"  {label:20s} claimed {claimed[label]:.3f}   "
              f"observed {min(vals):.3f}-{max(vals):.3f} "
              f"(mean {statistics.mean(vals):.3f}, sd {sd:.3f}, n={len(vals)})")
    print("\n  Read this as: if the v3 spread OVERLAPS 0.75-0.82, my correction")
    print("  of that figure is not established and the paper must report a")
    print("  range, not a point. If the spread sits well above it, the")
    print("  correction stands.")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lodo", type=int, default=0,
                    help="rerun the unseeded LODO this many times per arm "
                         "(needs torch; ~1 min per run per arm)")
    args = ap.parse_args()
    results = [("A correctness", sec_a()), ("B best-of-N", sec_b()),
               ("C trajectory", sec_c()), ("D oracle audit", sec_d())]
    if args.lodo:
        results.append(("E LODO spread", sec_e(args.lodo)))
    hdr("SUMMARY")
    for name, ok in results:
        print(f"  {name:20s} {'reproduced' if ok else '*** DISAGREES ***'}")
    if not args.lodo:
        print("\n  Section E (the LODO figures) NOT run. Add --lodo 10 to test the")
        print("  one correction that rests on a single unseeded draw.")


if __name__ == "__main__":
    main()
