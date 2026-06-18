#!/usr/bin/env python3
"""
sweep_catalog.py  -  Phase-2 silicon Fmax of the whole catalog (runs ON the Z2).

Loads the catalog bitstream (gen_catalog_bitstream.py) and, in one board
session, sweeps the PS clock and measures the real silicon Fmax of every design
plus the canary, reusing the Phase-0-validated sweep/score machinery
(clock_sweep_fmax.py). Prints a per-design table: silicon Fmax, the canary
ceiling, and -- if the laptop's rtl/accel_variants/ppa.jsonl is present -- the
Vivado v0 Fmax and the silicon/Vivado ratio.

Gate (the Phase-0 lesson, applied per design): every design's silicon Fmax must
sit below the canary's by a clear margin, else that design's number is the
harness, not the DUT.

Run on the board (as root):
  sudo /usr/local/share/pynq-venv/bin/python3 sweep_catalog.py \
      --bit rtl/catalog/out/system_catalog.bit --lo 30 --hi 200 --step 5 --runs 3
"""

import os
import json
import argparse

import numpy as np

import clock_sweep_fmax as CS
from capture_waveforms import _init_pynq, capture_one

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bit", default="rtl/catalog/out/system_catalog.bit")
    ap.add_argument("--sels", default=os.path.join(HERE, "rtl", "catalog",
                                                   "catalog_sels.json"))
    ap.add_argument("--ppa", default=os.path.join(HERE, "rtl", "accel_variants",
                                                  "ppa.jsonl"),
                    help="laptop run_ppa output, for the Vivado-ratio column")
    ap.add_argument("--lo", type=float, default=30.0)
    ap.add_argument("--hi", type=float, default=200.0)
    ap.add_argument("--step", type=float, default=5.0)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--depth", type=int, default=2048)
    ap.add_argument("--n-score", type=int, default=1024)
    ap.add_argument("--max-shift", type=int, default=8)
    ap.add_argument("--threshold", type=float, default=0.99)
    ap.add_argument("--canary-margin", type=float, default=20.0)
    ap.add_argument("--la-base", type=lambda x: int(x, 0), default=0x40000000)
    ap.add_argument("--out", default="rtl/catalog/catalog_fmax.json")
    args = ap.parse_args()

    sels_map = json.load(open(args.sels))            # name -> {sel, role}
    names = list(sels_map)
    sels = {n: sels_map[n]["sel"] for n in names}
    canary = next((n for n in names if sels_map[n]["role"] == "canary"), None)

    n_g = args.n_score + args.max_shift + CS.HEAD_SKIP + 4
    goldens = {n: CS.load_golden(n, n_g) for n in names}
    masks = {n: 0xFFFF for n in names}

    # optional Vivado v0 Fmax for the ratio column
    vivado = {}
    if os.path.exists(args.ppa):
        for line in open(args.ppa):
            try:
                p = json.loads(line)
            except ValueError:
                continue
            m = p.get("module", "")
            if m.endswith("__v0") and p.get("compiled"):
                vivado[m[:-4]] = p.get("fmax_mhz", 0.0)

    _init_pynq()
    from pynq import Overlay, MMIO
    print(f"loading {args.bit}")
    Overlay(args.bit)
    mmio = MMIO(args.la_base, 0x10000)

    freqs = []
    f = args.lo
    while f <= args.hi + 1e-6:
        freqs.append(round(f, 2))
        f += args.step

    # per design: list of measured Fmax over runs
    fmaxes = {n: [] for n in names}
    for r in range(args.runs):
        print(f"\n=== run {r + 1}/{args.runs} ({args.lo}-{args.hi} MHz) ===")
        res = CS.sweep_once(mmio, freqs, goldens, masks, sels,
                            args.depth, args.n_score, args.max_shift,
                            args.threshold)
        for n in names:
            if res[n]["fmax"] is not None:
                fmaxes[n].append(res[n]["fmax"])
            print(f"  {n:10s} Fmax = {res[n]['fmax']} MHz "
                  f"(first fail {res[n]['first_fail']})")

    can_med = float(np.median(fmaxes[canary])) if canary and fmaxes[canary] else None

    print("\n" + "=" * 66)
    print(f"{'design':10s} {'sil Fmax':>9s} {'spread':>7s} {'Vivado v0':>10s} "
          f"{'ratio':>6s}  gate")
    print("-" * 66)
    table = {}
    for n in names:
        if not fmaxes[n]:
            print(f"{n:10s}  (never passed/failed in range)")
            continue
        med = float(np.median(fmaxes[n]))
        spread = float(max(fmaxes[n]) - min(fmaxes[n]))
        viv = vivado.get(n)
        ratio = (med / viv) if viv else None
        if sels_map[n]["role"] == "canary":
            gate = "harness ref"
        elif can_med is not None and (can_med - med) >= args.canary_margin:
            gate = "OK"
        else:
            gate = "TOO CLOSE TO CANARY"
        table[n] = {"silicon_fmax": med, "spread": spread,
                    "vivado_v0": viv, "ratio": ratio, "gate": gate}
        vs = f"{viv:10.1f}" if viv else f"{'-':>10s}"
        rs = f"{ratio:6.2f}" if ratio else f"{'-':>6s}"
        print(f"{n:10s} {med:9.1f} {spread:7.1f} {vs} {rs}  {gate}")

    json.dump({"args": vars(args), "table": table, "canary_median": can_med},
              open(args.out, "w"), indent=1)
    print(f"\nfull data -> {args.out}")
    print("Per-design gate OK = silicon Fmax is the DUT's, not the harness.")


if __name__ == "__main__":
    main()
