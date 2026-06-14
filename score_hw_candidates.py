#!/usr/bin/env python3
"""
score_hw_candidates.py  -  Runs ON the PYNQ-Z2.  The silicon half of the gap.

For each candidate packed by gen_candidate_bitstream.py: load its batch
bitstream, capture the candidate running on real fabric, and score that
capture against the design's golden -- the HARDWARE reward.  Paired with the
simulation reward already in the candidate manifest, the difference is the
simulation/silicon reward gap.

The stimulus counter free-runs (not reset on arm), so the capture is a window
of the candidate's behaviour at an unknown phase; the hardware reward is the
best masked-Hamming similarity to the golden over all phases (a correct
candidate aligns to ~1.0; a candidate that behaves differently on silicon than
the golden cannot, no matter the phase).

Run on the board (PYNQ image, as root):
    sudo python3 score_hw_candidates.py \
        --bit-dir rtl/cand_batches \
        --manifest rtl/cand_batches/cand_manifest.json \
        --out rtl/cand_batches/cand_gap.jsonl

Off-board afterwards: analyze_gap.py for the headline numbers.
"""

import os
import json
import argparse

import numpy as np

import score_candidate as SC
from capture_waveforms import _init_pynq, capture_one

HEAD_SKIP = 4


def hw_reward(capture, rec, n_score, max_phase):
    """Best masked-Hamming similarity of the capture to the golden, any phase."""
    mask = rec["probe_mask"]
    hwm = (capture & mask).astype(np.uint16)[HEAD_SKIP:HEAD_SKIP + n_score]
    m = len(hwm)
    if m < 16:
        return 0.0
    P = max(2, rec["period"])
    span = int(min(max(2 * P, 4096), max_phase))
    gold = (SC.golden_from_body(rec["golden_body"], span + m)
            & mask).astype(np.uint16)
    best = 0.0
    for off in range(span):
        s = SC.hamming_similarity(hwm, gold[off:off + m], mask)
        if s > best:
            best = s
            if best >= 0.9999:
                break
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bit-dir", default="rtl/cand_batches")
    ap.add_argument("--manifest", default="rtl/cand_batches/cand_manifest.json")
    ap.add_argument("--out", default="rtl/cand_batches/cand_gap.jsonl")
    ap.add_argument("--la-base", type=lambda x: int(x, 0), default=0x40000000)
    ap.add_argument("--depth", type=int, default=8192,
                    help="capture samples to read per candidate")
    ap.add_argument("--n-score", type=int, default=1024,
                    help="samples actually scored (<= depth)")
    ap.add_argument("--max-phase", type=int, default=4096,
                    help="phase offsets searched for best alignment")
    args = ap.parse_args()

    _init_pynq()
    from pynq import Overlay, MMIO

    man = json.load(open(args.manifest))
    manifest = SC.load_manifest()
    by_batch = {}
    for d in man["designs"]:
        by_batch.setdefault(d["batch"], []).append(d)

    done = set()
    if os.path.exists(args.out):
        for line in open(args.out):
            try:
                done.add(json.loads(line)["module"])
            except (ValueError, KeyError):
                pass

    total, scored = 0, 0
    with open(args.out, "a") as fout:
        for batch_id in sorted(by_batch):
            bit = os.path.join(args.bit_dir, f"out_cb{batch_id}",
                               f"system_cb{batch_id}.bit")
            if not os.path.exists(bit):
                print(f"[batch {batch_id}] missing {bit} -- SKIP")
                continue
            print(f"[batch {batch_id}] loading {bit}")
            Overlay(bit)
            mmio = MMIO(args.la_base, 0x10000)
            for d in sorted(by_batch[batch_id], key=lambda x: x["local_sel"]):
                total += 1
                if d["module"] in done:
                    continue
                rec = manifest[d["design"]]
                try:
                    cap = capture_one(mmio, d["local_sel"], args.depth)
                    hwr = hw_reward(cap, rec, args.n_score, args.max_phase)
                except Exception as e:
                    print(f"   [{d['module']}] FAIL: {e}")
                    continue
                fout.write(json.dumps({
                    "module": d["module"], "design": d["design"],
                    "family": d["family"], "sim_reward": d["sim_reward"],
                    "hw_reward": hwr, "gap": d["sim_reward"] - hwr,
                }) + "\n")
                fout.flush()
                scored += 1
                if scored % 25 == 0:
                    print(f"   scored {scored} ...")
    print(f"\nDONE: scored {scored}/{total} candidates -> {args.out}")


if __name__ == "__main__":
    main()
