#!/usr/bin/env python3
"""
collect_hls.py  -  Phase D1: parse the Vitis HLS baseline runs and print the
HLS-vs-LLM comparison table on the held-out designs.

Numbers used:
  * HLS Fmax  = real post-implementation achieved clock (export_design -flow
    impl report: "CP achieved post-implementation"), NOT the csynth estimate.
  * HLS II    = initiation interval from csynth.xml (samples every II cycles).
  * Throughput (Msample/s) = Fmax / II  -- the honest comparison unit, since
    our RTL designs are all II=1 (one sample per cycle) while nopragma HLS is
    typically II>1.
  * LLM columns = freq-weighted real Vivado Fmax from rtl/holdout_eval
    (ppa.jsonl + fmax_manifest.json), same laptop/tool/period as the HLS runs.

    python collect_hls.py            # from the repo root (or hls_baseline/)
"""

import os
import re
import json
import glob
import argparse
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
HLS = os.path.join(HERE, "rtl", "hls_baseline")
EVAL = os.path.join(HERE, "rtl", "holdout_eval")


def parse_hls(design, variant):
    proj = os.path.join(HLS, f"proj_{design}_{variant}", "sol1")
    out = {"fmax": None, "ii": None, "lut": None, "ff": None, "dsp": None}
    # real post-impl clock from the export report
    for rpt in glob.glob(os.path.join(proj, "impl", "report", "**", "*_export.rpt"),
                         recursive=True):
        txt = open(rpt, errors="replace").read()
        m = re.search(r"CP achieved post-implementation:\s*([\d.]+)", txt)
        if m:
            out["fmax"] = round(1000.0 / float(m.group(1)), 1)
        for k, pat in (("lut", r"LUT:\s*(\d+)"), ("ff", r"FF:\s*(\d+)"),
                       ("dsp", r"DSP:\s*(\d+)")):
            mm = re.search(pat, txt)
            if mm:
                out[k] = int(mm.group(1))
    # initiation interval from csynth.xml
    for xml in glob.glob(os.path.join(proj, "syn", "report", "csynth.xml")):
        txt = open(xml, errors="replace").read()
        m = re.search(r"<Interval-max>(\d+)</Interval-max>", txt)
        if m:
            out["ii"] = int(m.group(1))
    return out


def llm_columns():
    """(design) -> {sft_med, grpo_top} real Vivado Fmax from the held-out eval."""
    mani_p = os.path.join(EVAL, "fmax_manifest.json")
    ppa_p = os.path.join(EVAL, "ppa.jsonl")
    if not (os.path.exists(mani_p) and os.path.exists(ppa_p)):
        return {}
    mani = json.load(open(mani_p))
    fmax = {}
    for line in open(ppa_p):
        try:
            p = json.loads(line)
        except ValueError:
            continue
        if p.get("compiled"):
            fmax[p["module"]] = float(p.get("fmax_mhz", 0.0))
    rows = defaultdict(lambda: defaultdict(list))   # design -> policy -> [(f,cnt)]
    for mod, info in mani.items():
        if mod in fmax:
            rows[info["design"]][info["policy"]].append((fmax[mod], info["count"]))
    out = {}
    for d, pol in rows.items():
        o = {}
        if "grpo" in pol:
            o["grpo_top"] = max(f for f, _ in pol["grpo"])
        if "sft" in pol:
            exp = sorted(f for f, c in pol["sft"] for _ in range(c))
            o["sft_med"] = exp[len(exp) // 2] if exp else None
        out[d] = o
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HLS, "hls_results.json"))
    args = ap.parse_args()

    designs = sorted({re.sub(r"^proj_|_(pragma|nopragma)$", "", os.path.basename(p))
                      for p in glob.glob(os.path.join(HLS, "proj_*"))})
    if not designs:
        raise SystemExit("no proj_* dirs in rtl/hls_baseline -- run "
                         "vitis_hls -f run_hls.tcl first")
    llm = llm_columns()

    print(f"{'design':13s} | {'HLS naive F/II->thr':>21s} | "
          f"{'HLS pragma F/II->thr':>21s} | {'sft med':>8s} | {'GRPO top':>8s} | "
          f"{'grpo/hls':>8s}")
    print("-" * 100)
    table = {}
    ratios = []
    for d in designs:
        nop = parse_hls(d, "nopragma")
        prg = parse_hls(d, "pragma")
        l = llm.get(d, {})
        def thr(v):
            if v["fmax"] and v["ii"]:
                return v["fmax"] / v["ii"]
            return None
        tn, tp = thr(nop), thr(prg)
        g = l.get("grpo_top")
        ratio = (g / tp) if (g and tp) else None
        if ratio:
            ratios.append(ratio)
        table[d] = {"hls_nopragma": nop, "hls_pragma": prg, **l,
                    "thr_nopragma": tn, "thr_pragma": tp, "grpo_over_hls": ratio}
        f = lambda x, w=6: f"{x:{w}.1f}" if x is not None else " " * (w - 1) + "-"
        print(f"{d:13s} | {f(nop['fmax'])}/{nop['ii'] or '-':>2} ->{f(tn)} | "
              f"{f(prg['fmax'])}/{prg['ii'] or '-':>2} ->{f(tp)} | "
              f"{f(l.get('sft_med'), 8)} | {f(g, 8)} | {f(ratio, 8)}")
    if ratios:
        gm = 1.0
        for r in ratios:
            gm *= r
        gm **= (1.0 / len(ratios))
        print("-" * 100)
        print(f"geomean GRPO-throughput / HLS-pragma-throughput over "
              f"{len(ratios)} designs: {gm:.2f}x")
    json.dump(table, open(args.out, "w"), indent=1)
    print(f"\nfull data -> {args.out}")
    print("Framing reminder: HLS input is C++ written by an engineer; our input "
          "is an NL spec. The comparison bounds quality, it does not replace it.")


if __name__ == "__main__":
    main()
