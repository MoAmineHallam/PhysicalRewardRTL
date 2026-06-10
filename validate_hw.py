#!/usr/bin/env python3
"""
validate_hw.py  -  Confirm captured hardware waveforms match the golden RTL.

After capture_waveforms.py, this compares each rtl_library/<name>/waveform.npy
against the manifest golden_body. The stimulus counter in dut_top free-runs
(it is NOT reset when the LA arms), so each capture starts at an unknown cnt
phase c0. Since the whole fabric (cnt + DUT state) evolves deterministically
from the boot reset, hw[i] == golden[c0 + i]: the capture is an exact window
of the golden sequence at an unknown offset.

Validation therefore searches the full design period for a phase at which the
capture matches the golden EXACTLY (masked to the probe bits). Three verdicts:

  good        - exact match found at some phase            -> usable for reward
  bad         - no phase matches (real synthesis/wiring bug) -> exclude
  long_period - period > capture depth, phase unrecoverable  -> exclude
                (or rebuild with reset-on-arm hardware to validate these)

Usage:
    python validate_hw.py                 # validate every captured design
    python validate_hw.py --report hw_bad.json
"""

import os
import json
import argparse

import numpy as np

RTL_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rtl_library")

# Samples to skip at the head of each capture: the sel mux switches at arm
# time, so the first few samples can carry the previously-selected DUT.
HEAD_SKIP = 4
# Probe length used to find candidate phases before full verification.
PROBE_LEN = 64


def golden_from_body(body, n):
    fixed = ("def _g(n):\n"
             "    import numpy as np\n"
             "    out = []\n"
             "    for c in range(n):\n"
             + body.rstrip("\n") + "\n"
             "        out.append(val & 0xFFFF)\n"
             "    return np.array(out, dtype=np.uint16)\n")
    ns = {}
    exec(fixed, ns)
    return ns["_g"](n)


def find_phase(hw, rec):
    """Exact-match phase search of hw inside the periodic golden sequence.

    Returns (verdict, phase) where verdict is 'good', 'bad' or 'long_period'.
    """
    mask = rec["probe_mask"]
    period = rec["period"]
    n = len(hw)
    hwm = (hw & mask).astype(np.uint16)[HEAD_SKIP:]
    m = len(hwm)

    if period > n:
        # capture window holds less than one period: cannot recover the phase
        return "long_period", None

    # Golden long enough that any start t in [period, 2*period) plus the
    # capture length stays in-bounds; [0, period) is skipped so the golden's
    # reset transient never lands inside the comparison window.
    gold = golden_from_body(rec["golden_body"], 2 * period + n)
    goldm = (gold & mask).astype(np.uint16)

    probe_len = min(PROBE_LEN, m)
    probe = hwm[:probe_len]
    windows = np.lib.stride_tricks.sliding_window_view(
        goldm[period:2 * period + probe_len - 1], probe_len)[:period]
    cand = np.nonzero((windows == probe).all(axis=1))[0]
    for t in cand:
        start = period + t
        if np.array_equal(goldm[start:start + m], hwm):
            return "good", int(t)
    return "bad", None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    man = json.load(open(os.path.join(RTL_LIB, "manifest.json")))

    checked, good, bad, longp = 0, [], [], []
    for rec in man:
        name = rec["name"]
        wf = os.path.join(RTL_LIB, name, "waveform.npy")
        if not os.path.exists(wf):
            continue
        checked += 1
        hw = np.load(wf)
        verdict, _ = find_phase(hw, rec)
        {"good": good, "bad": bad, "long_period": longp}[verdict].append(name)
        if checked % 100 == 0:
            print(f"  ... {checked} checked")

    print(f"Validated {checked} captured designs: {len(good)} match, "
          f"{len(bad)} mismatch, {len(longp)} long-period (unverifiable)")
    if bad:
        print("MISMATCH (exclude from reward set):")
        for n in bad[:50]:
            print(f"   {n}")
    if longp:
        print(f"LONG PERIOD ({len(longp)}, period > capture depth; exclude or "
              "rebuild with reset-on-arm):")
        for n in longp[:20]:
            print(f"   {n}")
    if args.report:
        json.dump({"good": good, "bad": bad, "long_period": longp},
                  open(args.report, "w"), indent=1)
        print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
