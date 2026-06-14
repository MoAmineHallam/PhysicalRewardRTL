#!/usr/bin/env python3
"""
verify_gap.py  -  Control for the sim/silicon reward gap.

The dataset sim_reward and the silicon hw_reward were computed with DIFFERENT
scorers (4096 cycles + 3 registration shifts vs 1024 samples + 4096-offset
phase search). A fair gap must use ONE scorer that differs only in ENGINE
(iverilog vs FPGA fabric). This re-simulates each flagged candidate and scores
the simulation waveform with the SAME function used on silicon
(score_hw_candidates.hw_reward):

    gap_clean = hw_reward(silicon) - hw_reward(simulation)     [identical scorer]

Gaps that SURVIVE  -> real sim/silicon behavioral differences (reset/GSR,
                      X-optimism, synthesis vs simulation semantics).
Gaps that VANISH   -> artifacts of the original mismatched scoring (phase
                      search asymmetry, different cycle counts).

Run on the server (needs iverilog + the candidate RTL in dataset.jsonl):
    cd /zeng_gk/Amine/mas
    python fpga/verify_gap.py --gap cand_gap.jsonl --dataset fpga/dataset.jsonl
"""

import os
import sys
import json
import argparse
import tempfile
import collections

import score_candidate as SC
# top-level import is pynq-free (Overlay/MMIO are imported inside main there)
from score_hw_candidates import hw_reward


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", required=True, help="cand_gap.jsonl from the board")
    ap.add_argument("--dataset", required=True, help="dataset.jsonl (candidate RTL)")
    ap.add_argument("--threshold", type=float, default=0.1)
    ap.add_argument("--n-score", type=int, default=1024)
    ap.add_argument("--max-phase", type=int, default=4096)
    ap.add_argument("--cycles", type=int, default=4096)
    ap.add_argument("--out", default="gap_verified.jsonl")
    args = ap.parse_args()

    man = SC.load_manifest()
    rtls = collections.defaultdict(list)
    for line in open(args.dataset):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        rtls[r["design"]].append(r["rtl"])

    flagged = [g for g in (json.loads(l) for l in open(args.gap))
               if abs(g["gap"]) > args.threshold]
    print(f"re-scoring {len(flagged)} flagged candidates with the identical "
          f"(silicon) scorer\n")

    fout = open(args.out, "w")
    survived = under = over = 0
    n = 0
    for g in flagged:
        module, design = g["module"], g["design"]
        try:
            idx = int(module[1:].split("_", 1)[0])     # c<idx>_<design>
            rtl = rtls[design][idx]
        except (ValueError, KeyError, IndexError):
            continue
        rec = man[design]
        with tempfile.NamedTemporaryFile(suffix=".v", mode="w",
                                         delete=False) as f:
            f.write(rtl)
            path = f.name
        try:
            sim_wave = SC.simulate(path, rec, args.cycles)
            sim_hw = hw_reward(sim_wave, rec, args.n_score, args.max_phase)
        except Exception:
            sim_hw = None
        finally:
            os.unlink(path)
        if sim_hw is None:
            print(f"{module:24s}  (sim failed, skipped)")
            continue
        n += 1
        clean = g["hw_reward"] - sim_hw
        if abs(clean) > args.threshold:
            survived += 1
            under += clean < 0
            over += clean > 0
        fout.write(json.dumps({**g, "sim_hw_reward": sim_hw,
                               "gap_clean": clean}) + "\n")
        flag = "SURVIVES" if abs(clean) > args.threshold else "artifact"
        print(f"{module:24s} sim_same={sim_hw:.2f} silicon={g['hw_reward']:.2f}"
              f"  gap_orig={g['gap']:+.2f} gap_clean={clean:+.2f}  {flag}")
    fout.close()

    print(f"\n{survived}/{n} flagged gaps SURVIVE identical scoring "
          f"(real sim/silicon differences):")
    print(f"   sim under-rewards (silicon right): {under}")
    print(f"   sim over-rewards  (silicon catches defect): {over}")
    print(f"the remaining {n - survived} were scoring-method artifacts.")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
