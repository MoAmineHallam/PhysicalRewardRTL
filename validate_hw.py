#!/usr/bin/env python3
"""
validate_hw.py  -  Confirm captured hardware waveforms match the golden RTL.

After capture_waveforms.py, this compares each rtl_library/<name>/waveform.npy
against the manifest golden_body (masked, with reset/registration offset search).
Designs that disagree indicate a synthesis/timing/probe-wiring issue and must be
excluded from the reward set.

Usage:
    python validate_hw.py                 # validate every captured design
    python validate_hw.py --report bad.json
"""

import os
import json
import argparse

import numpy as np

RTL_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rtl_library")


def golden_from_body(body, n):
    src = ("def _g(n):\n import numpy as np\n out=[]\n for c in range(n):\n"
           + body.rstrip("\n") + "\n  out.append(val & 0xFFFF)\n"
           " return np.array(out,dtype=np.uint16)\n")
    # body lines carry 8 spaces; re-base to 2 here
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


def aligned_equal(hw, gold, mask):
    hw = (hw & mask).astype(np.uint16)
    gold = (gold & mask).astype(np.uint16)
    n = min(len(hw), len(gold))
    hw, gold = hw[:n], gold[:n]
    # try registration/reset offsets
    for shift in (1, 2, 0, 3):
        g = np.roll(gold, -shift)
        m = n - shift
        if m > 16 and np.array_equal(hw[:m - 1], g[:m - 1]):
            return True, shift
    return False, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=None)
    args = ap.parse_args()

    man = json.load(open(os.path.join(RTL_LIB, "manifest.json")))
    by_name = {r["name"]: r for r in man}

    checked, good, bad = 0, [], []
    for name, rec in by_name.items():
        wf = os.path.join(RTL_LIB, name, "waveform.npy")
        if not os.path.exists(wf):
            continue
        checked += 1
        hw = np.load(wf)
        gold = golden_from_body(rec["golden_body"], len(hw))
        ok, shift = aligned_equal(hw, gold, rec["probe_mask"])
        (good if ok else bad).append(name)

    print(f"Validated {checked} captured designs: {len(good)} match, "
          f"{len(bad)} mismatch")
    if bad:
        print("MISMATCH (exclude from reward set):")
        for n in bad[:50]:
            print(f"   {n}")
    if args.report:
        json.dump({"good": good, "bad": bad}, open(args.report, "w"), indent=1)
        print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
