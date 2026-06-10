#!/usr/bin/env python3
"""
build_dataset.py  -  Stage 7 RL dataset builder (manifest-driven, all designs).

For every hardware-validated design (hw_bad.json["good"], from stage 6):
generate N candidates with RTLCoder from the design's spec.txt, score each
with score_candidate (dense Hamming reward against the silicon-certified
golden), append JSONL records.

Runs on the GPU server (needs /zeng_gk/Amine/mas on sys.path for llm.py).

Usage:
    python build_dataset.py                          # all good designs
    python build_dataset.py --n 20 --temp 0.9
    python build_dataset.py --designs mod7_counter acc2to8
    python build_dataset.py --start 0 --limit 200    # shard a long run
    python build_dataset.py --out dataset.jsonl      # append + resume:
                                                     # designs that already
                                                     # have >= n records are
                                                     # skipped

Record format (one JSON object per line):
    {"design": str, "family": str, "reward": float, "compile_ok": bool,
     "rtl": str}
reward is 0.0 when the candidate fails to compile/simulate.
"""

import os
import sys
import json
import argparse
import collections

import score_candidate as SC

HERE = os.path.dirname(os.path.abspath(__file__))
LLM_DIR = "/zeng_gk/Amine/mas"
sys.path.insert(0, LLM_DIR)


def extract_verilog(text, module_name):
    """Extract first complete Verilog module from LLM output."""
    import re
    m = re.search(rf"(?s)(module\s+{re.escape(module_name)}\b.*?endmodule)",
                  text)
    if m:
        return m.group(1)
    m = re.search(r"(?s)(module\s+\w+\b.*?endmodule)", text)
    if m:
        return m.group(1)
    return None


def load_pool(hw_report):
    """Hardware-validated designs that have a spec.txt, manifest order."""
    man = SC.load_manifest()
    good = SC.load_good_names(hw_report)
    pool = []
    for name, rec in man.items():
        if name not in good:
            continue
        spec_path = os.path.join(SC.RTL_LIB, name, "spec.txt")
        if not os.path.exists(spec_path):
            print(f"[warn] {name}: spec.txt missing, skipped", file=sys.stderr)
            continue
        pool.append((rec, open(spec_path).read()))
    return pool


def existing_counts(out_path):
    counts = collections.Counter()
    if os.path.exists(out_path):
        for line in open(out_path):
            try:
                counts[json.loads(line)["design"]] += 1
            except (ValueError, KeyError):
                pass
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20,
                    help="candidates per design")
    ap.add_argument("--temp", type=float, default=0.9)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--cycles", type=int, default=SC.N_CYCLES_DEFAULT,
                    help="simulation cycles per score")
    ap.add_argument("--out", default="dataset.jsonl")
    ap.add_argument("--hw-report", default=SC.HW_REPORT)
    ap.add_argument("--designs", nargs="*", default=None,
                    help="restrict to these design names")
    ap.add_argument("--start", type=int, default=0,
                    help="skip the first START designs of the pool")
    ap.add_argument("--limit", type=int, default=None,
                    help="process at most LIMIT designs")
    args = ap.parse_args()

    from llm import coder_call  # GPU server only

    pool = load_pool(args.hw_report)
    if args.designs:
        keep = set(args.designs)
        pool = [(r, s) for r, s in pool if r["name"] in keep]
    pool = pool[args.start:]
    if args.limit is not None:
        pool = pool[:args.limit]
    done = existing_counts(args.out)
    manifest = SC.load_manifest()

    print(f"pool: {len(pool)} hardware-validated designs, "
          f"{args.n} candidates each -> {args.out}", flush=True)

    with open(args.out, "a") as fout:
        for di, (rec, spec) in enumerate(pool):
            name = rec["name"]
            need = args.n - done.get(name, 0)
            if need <= 0:
                continue
            print(f"[{di + 1}/{len(pool)}] {name}: generating {need}",
                  flush=True)
            messages = [{"role": "user", "content": spec}]
            stats = []
            for i in range(need):
                try:
                    raw = coder_call(messages, max_tokens=args.max_tokens,
                                     temperature=args.temp)
                except Exception as e:
                    print(f"   [gen {i}] call failed: {e}", file=sys.stderr)
                    continue
                rtl = extract_verilog(raw, name)
                if rtl is None:
                    rtl, reward, ok = raw[-2000:], 0.0, False
                else:
                    rtl = rtl.encode("ascii", errors="replace").decode("ascii")
                    try:
                        reward = SC.score_rtl(rtl, name, args.cycles, manifest)
                        ok = True
                    except RuntimeError:
                        reward, ok = 0.0, False
                fout.write(json.dumps({
                    "design": name, "family": rec["family"],
                    "reward": reward, "compile_ok": ok, "rtl": rtl,
                }) + "\n")
                fout.flush()
                stats.append(reward)
            if stats:
                print(f"   rewards: mean={sum(stats) / len(stats):.3f} "
                      f"max={max(stats):.3f} "
                      f"compile_ok={sum(s > 0 for s in stats)}/{len(stats)}",
                      flush=True)

    print("done.")


if __name__ == "__main__":
    main()
