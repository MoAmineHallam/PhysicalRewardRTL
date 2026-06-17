#!/usr/bin/env python3
"""
clock_sweep_fmax.py  -  Phase-0 silicon-Fmax feasibility spike.  Runs ON the
PYNQ-Z2.  This is the GO/NO-GO gate for the whole silicon-Fmax direction.

It loads the spike bitstream (fir16_8b on sel 0, echo8b canary on sel 1), then
sweeps the PS fabric clock (Clocks.fclk0_mhz) upward.  At each frequency it
captures both DUTs (reset-on-arm) and scores them against their goldens.  As the
clock rises, the FIR's deep multiply-accumulate path eventually violates timing
and its capture diverges from the golden; the canary, a pure flip-flop chain
sharing the same capture/AXI tail, keeps matching far higher.

  silicon Fmax(DUT) = highest swept frequency at which score(DUT) >= threshold,
                      i.e. (first failing frequency) - step.

GATE (printed at the end -- ALL must hold to justify building the catalog):
  1. canary Fmax  -  FIR Fmax  >=  --canary-margin  (default 20 MHz)
       else: the harness, not the FIR, is the bottleneck -> FIX THE HARNESS.
  2. FIR Fmax repeatable within +/- --repeat-tol (default 5 MHz) across --runs.
  3. FIR Fmax / Vivado-STA Fmax in a plausible range (1.0 - 2.2x; room-temp
     silicon beats worst-case signoff by up to ~2x) -- pass the STA number via
     --vivado-fmax (from run_ppa on rtl_library/fir16_8b).

Run on the board (PYNQ image, as root):
  sudo /usr/local/share/pynq-venv/bin/python3 clock_sweep_fmax.py \
      --bit rtl/spike/out/system_spike.bit \
      --lo 60 --hi 260 --step 5 --runs 3 --vivado-fmax 165
"""

import os
import time
import json
import argparse
import importlib.util

import numpy as np

import score_candidate as SC
from capture_waveforms import _init_pynq, capture_one

ROOT = os.path.dirname(os.path.abspath(__file__))
HEAD_SKIP = 4


def load_golden(name, n):
    path = os.path.join(ROOT, "rtl_library", name, "golden.py")
    spec = importlib.util.spec_from_file_location("g_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.compute_golden(n).astype(np.uint16)


def best_similarity(capture, golden, mask, n_score, max_shift):
    """Masked-Hamming similarity, best over a small TWO-SIDED registration shift
    (the hardware pipeline delay can land on either side of the ideal golden)."""
    hwm = (capture & mask).astype(np.uint16)[HEAD_SKIP:HEAD_SKIP + n_score]
    if len(hwm) < 16:
        return 0.0
    g = (golden & mask).astype(np.uint16)
    best = 0.0
    for sh in range(max_shift + 1):
        for a, b in ((hwm, g[sh:]), (hwm[sh:], g)):
            k = min(len(a), len(b))
            if k < 16:
                continue
            s = SC.hamming_similarity(a[:k], b[:k], mask)
            if s > best:
                best = s
    return best


def set_clock(target_mhz):
    """Set FCLK0 and return the ACTUAL achieved frequency (PLL snaps)."""
    from pynq import Clocks
    Clocks.fclk0_mhz = float(target_mhz)
    time.sleep(0.05)                       # PLL relock + settle
    return float(Clocks.fclk0_mhz)


def sweep_once(mmio, freqs, goldens, masks, sels, depth, n_score,
               max_shift, thr):
    """One full sweep. Returns dict: name -> {fmax, rows:[(freq,score)...]}."""
    res = {nm: {"fmax": None, "first_fail": None, "rows": []} for nm in sels}
    failed = set()
    for target in freqs:
        actual = set_clock(target)
        for nm, sel in sels.items():
            cap = capture_one(mmio, sel, depth)
            score = best_similarity(cap, goldens[nm], masks[nm],
                                    n_score, max_shift)
            res[nm]["rows"].append((round(actual, 2), round(score, 4)))
            if score >= thr and nm not in failed:
                res[nm]["fmax"] = round(actual, 2)
            elif score < thr and nm not in failed:
                failed.add(nm)
                res[nm]["first_fail"] = round(actual, 2)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bit", default="rtl/spike/out/system_spike.bit")
    ap.add_argument("--fir-name", default="fir16_8b")
    ap.add_argument("--canary-name", default="echo8b")
    ap.add_argument("--fir-sel", type=int, default=0)
    ap.add_argument("--canary-sel", type=int, default=1)
    ap.add_argument("--lo", type=float, default=60.0)
    ap.add_argument("--hi", type=float, default=260.0)
    ap.add_argument("--step", type=float, default=5.0)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--depth", type=int, default=2048,
                    help="capture samples; must be <= the LA buffer DEPTH "
                         "(la_axi_fast = 2048)")
    ap.add_argument("--n-score", type=int, default=1024)
    ap.add_argument("--max-shift", type=int, default=8)
    ap.add_argument("--threshold", type=float, default=0.99)
    ap.add_argument("--canary-margin", type=float, default=20.0)
    ap.add_argument("--repeat-tol", type=float, default=5.0)
    ap.add_argument("--vivado-fmax", type=float, default=None,
                    help="Vivado STA Fmax (MHz) from run_ppa on the FIR, for the "
                         "silicon/STA ratio check")
    ap.add_argument("--la-base", type=lambda x: int(x, 0), default=0x40000000)
    ap.add_argument("--out", default="rtl/spike/sweep_result.json")
    args = ap.parse_args()

    _init_pynq()
    from pynq import Overlay, MMIO
    print(f"loading {args.bit}")
    Overlay(args.bit)
    mmio = MMIO(args.la_base, 0x10000)

    n_g = args.n_score + args.max_shift + HEAD_SKIP + 4
    goldens = {args.fir_name: load_golden(args.fir_name, n_g),
               args.canary_name: load_golden(args.canary_name, n_g)}
    masks = {args.fir_name: 0xFFFF, args.canary_name: 0xFFFF}
    sels = {args.fir_name: args.fir_sel, args.canary_name: args.canary_sel}

    freqs = []
    f = args.lo
    while f <= args.hi + 1e-6:
        freqs.append(round(f, 2))
        f += args.step

    all_runs = []
    fir_fmaxes, can_fmaxes = [], []
    for r in range(args.runs):
        print(f"\n=== sweep run {r + 1}/{args.runs} "
              f"({args.lo}-{args.hi} MHz, step {args.step}) ===")
        res = sweep_once(mmio, freqs, goldens, masks, sels,
                         args.depth, args.n_score, args.max_shift,
                         args.threshold)
        fir = res[args.fir_name]
        can = res[args.canary_name]
        print(f"  FIR    Fmax = {fir['fmax']} MHz (first fail {fir['first_fail']})")
        print(f"  canary Fmax = {can['fmax']} MHz (first fail {can['first_fail']})")
        all_runs.append(res)
        if fir["fmax"] is not None:
            fir_fmaxes.append(fir["fmax"])
        if can["fmax"] is not None:
            can_fmaxes.append(can["fmax"])

    # ---- GATE evaluation ----
    print("\n" + "=" * 60 + "\nPHASE-0 GATE\n" + "=" * 60)
    verdict = {"go": True, "reasons": []}

    if not fir_fmaxes or not can_fmaxes:
        verdict["go"] = False
        verdict["reasons"].append(
            "FIR or canary never passed/failed in range -- widen --lo/--hi.")
    else:
        fir_med = float(np.median(fir_fmaxes))
        can_med = float(np.median(can_fmaxes))
        fir_spread = float(max(fir_fmaxes) - min(fir_fmaxes))

        margin = can_med - fir_med
        ok1 = margin >= args.canary_margin
        print(f"[{'PASS' if ok1 else 'FAIL'}] canary margin: "
              f"canary {can_med} - FIR {fir_med} = {margin:.1f} MHz "
              f"(need >= {args.canary_margin})")
        if not ok1:
            verdict["go"] = False
            verdict["reasons"].append(
                "Canary fails too close to / before the FIR -> the capture "
                "harness is the bottleneck, not the FIR. Silicon Fmax is NOT "
                "attributable to the DUT. Fix the harness (cross DUT clock vs "
                "capture/AXI clock, or pipeline the capture path) before trusting "
                "any silicon Fmax number.")

        ok2 = fir_spread <= args.repeat_tol
        print(f"[{'PASS' if ok2 else 'FAIL'}] FIR repeatability: spread "
              f"{fir_spread:.1f} MHz across {len(fir_fmaxes)} runs "
              f"(need <= {args.repeat_tol})")
        if not ok2:
            verdict["go"] = False
            verdict["reasons"].append(
                "FIR Fmax not repeatable -> divergence point is noisy "
                "(metastable/PVT). Silicon Fmax reward would be noise.")

        if args.vivado_fmax:
            ratio = fir_med / args.vivado_fmax
            ok3 = 1.0 <= ratio <= 2.2
            print(f"[{'PASS' if ok3 else 'FAIL'}] silicon/STA ratio: "
                  f"{fir_med}/{args.vivado_fmax} = {ratio:.2f} "
                  f"(expect 1.0-2.2x; room-temp silicon beats worst-case "
                  f"signoff by up to ~2x)")
            if not ok3:
                verdict["go"] = False
                verdict["reasons"].append(
                    "Silicon/STA ratio implausible -> harness or STA mismatch; "
                    "investigate before trusting the number.")
        else:
            print("[SKIP] silicon/STA ratio: pass --vivado-fmax to check "
                  "(run_ppa on rtl_library/fir16_8b)")

    print("\nVERDICT:", "GO -- build the accelerator catalog (Phase 1)."
          if verdict["go"] else "NO-GO -- see reasons:")
    for why in verdict["reasons"]:
        print("  -", why)
    if not verdict["go"]:
        print("\nPivot: keep PPA Vivado-estimated (Phase 3a only); the paper "
              "still stands on that plus the existing silicon characterisation.")

    out = {"args": vars(args), "freqs": freqs, "runs": all_runs,
           "fir_fmaxes": fir_fmaxes, "canary_fmaxes": can_fmaxes,
           "verdict": verdict}
    with open(args.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"\nfull sweep data -> {args.out}")


if __name__ == "__main__":
    main()
