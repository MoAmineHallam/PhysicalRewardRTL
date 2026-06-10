#!/usr/bin/env python3
"""
validate_hw.py  -  Confirm captured hardware waveforms match the golden RTL.

After capture_waveforms.py, this compares each rtl_library/<name>/waveform.npy
against the manifest golden_body. The stimulus counter in dut_top free-runs
(it is NOT reset when the LA arms), so each capture starts at an unknown cnt
phase c0. Since the whole fabric (cnt + DUT state) evolves deterministically
from the boot reset, hw[i] == golden[c0 + i]: the capture is an exact window
of the golden sequence at an unknown offset.

Validation therefore searches for the capture window inside a long golden
sequence (exact masked match). The manifest `period` field is used only as a
fast-path hint -- it is WRONG for stateful families like acc/mac (it records
the input period, not the state period), so when the fast path misses we
re-search a golden of --max-period samples. Three verdicts:

  good        - exact match found at some phase             -> usable for reward
  bad         - golden is periodic within the search cap and the window is
                nowhere in it (real synthesis/wiring bug)   -> exclude
  long_period - golden not periodic within the search cap; phase
                unrecoverable -> exclude (or rebuild with reset-on-arm hw)

Usage:
    python validate_hw.py                 # validate every captured design
    python validate_hw.py --report hw_bad.json
    python validate_hw.py --max-period $((1<<23))   # search harder
"""

import os
import json
import argparse

import numpy as np

RTL_LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rtl_library")

# Samples to skip at the head of each capture: the sel mux switches at arm
# time, so the first few samples can carry the previously-selected DUT.
HEAD_SKIP = 4
# Up to this many positions are fully verified after prefix filtering.
MAX_FULL_VERIFY = 16


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


def _find_window(goldm, hwm):
    """True iff hwm appears (exactly) as a contiguous window of goldm."""
    m, L = len(hwm), len(goldm)
    if L < m:
        return False
    # Anchor the probe at the first transition in hwm: degenerate prefixes
    # (e.g. the long zero-runs ALUs emit for unused opcodes) match everywhere
    # and would swamp the candidate list.
    diffs = np.flatnonzero(hwm[1:] != hwm[:-1])
    if len(diffs) == 0:
        # constant capture window: look for an m-long constant run in goldm
        run = np.concatenate(([0], (goldm == hwm[0]).astype(np.int8), [0]))
        edges = np.diff(run)
        starts = np.flatnonzero(edges == 1)
        ends = np.flatnonzero(edges == -1)
        return bool(np.any(ends - starts >= m))
    ps = min(int(diffs[0]), m - 64)
    probe = hwm[ps:ps + 64]
    # candidate window starts p such that goldm[p+ps : p+ps+64] == probe
    idx = np.flatnonzero(goldm[ps:L - m + ps + 1] == probe[0])
    j = 1
    while j < 64 and len(idx) > MAX_FULL_VERIFY:
        idx = idx[goldm[idx + ps + j] == probe[j]]
        j += 1
    # strided filtering across the whole window for periodic content
    for j in range(0, m, 257):
        if len(idx) <= MAX_FULL_VERIFY:
            break
        idx = idx[goldm[idx + j] == hwm[j]]
    for t in idx[:MAX_FULL_VERIFY]:
        if np.array_equal(goldm[t:t + m], hwm):
            return True
    return False


def _true_period(goldm, n, w0=8192):
    """Smallest verified self-repeat distance of goldm past the transient,
    or None if goldm is not periodic within its own length."""
    L = len(goldm)
    if L <= w0 + n:
        w0 = 64
    # move the anchor to a transition so it can't sit inside a constant run
    diffs = np.flatnonzero(goldm[w0:w0 + n][1:] != goldm[w0:w0 + n][:-1])
    if len(diffs):
        w0 += int(diffs[0])
    plen = min(4096, L - w0 - 1)
    anchor = goldm[w0:w0 + plen]
    idx = np.flatnonzero(goldm[w0 + 1:L - plen] == anchor[0]) + w0 + 1
    # two-stage prefix filtering: ramp-like sequences carry many short false
    # repeats, so escalate the prefix length before giving up
    j = 1
    for stop, keep in ((64, 32), (plen, 4)):
        while j < stop and len(idx) > keep:
            idx = idx[goldm[idx + j] == anchor[j]]
            j += 1
        for p in idx[:32]:
            K = L - p
            if K >= n and np.array_equal(goldm[w0:w0 + K], goldm[p:p + K]):
                return int(p - w0)
    return None


def find_phase(hw, rec, cap):
    """Exact-match search of hw inside the golden sequence.

    Returns 'good', 'bad' or 'long_period'.
    """
    mask = rec["probe_mask"]
    P = max(2, rec["period"])
    n = len(hw)
    hwm = (hw & mask).astype(np.uint16)[HEAD_SKIP:]

    # fast path: listed period (correct for most families)
    if 2 * P + n <= (1 << 18):
        goldm = (golden_from_body(rec["golden_body"], 2 * P + n)
                 & mask).astype(np.uint16)
        if _find_window(goldm, hwm):
            return "good"

    # full search: listed period is unreliable (acc/mac understate it) and
    # many designs have true periods far beyond the capture depth
    goldm = (golden_from_body(rec["golden_body"], cap + n)
             & mask).astype(np.uint16)
    if _find_window(goldm, hwm):
        return "good"
    if _true_period(goldm, n) is not None:
        return "bad"          # searched a full period: window truly absent
    return "long_period"      # period exceeds cap: phase unrecoverable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default=None)
    ap.add_argument("--max-period", type=int, default=1 << 22,
                    help="golden search length for the slow path (samples)")
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
        verdict = find_phase(hw, rec, args.max_period)
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
        print(f"LONG PERIOD ({len(longp)}, period > search cap; exclude, "
              "raise --max-period, or rebuild with reset-on-arm):")
        for n in longp[:20]:
            print(f"   {n}")
    if args.report:
        json.dump({"good": good, "bad": bad, "long_period": longp},
                  open(args.report, "w"), indent=1)
        print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
