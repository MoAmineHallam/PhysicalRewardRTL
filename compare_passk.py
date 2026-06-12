#!/usr/bin/env python3
"""
compare_passk.py  -  Paired per-problem comparison of two pass@k runs.

Usage:
    python compare_passk.py fpga/passk_base.jsonl fpga/passk_grpo_v3.jsonl

Prints overall pass@1/5/10 for both runs, the paired delta, and the
per-problem table sorted by delta (which problems the second model fixed
or broke, and by how much), plus compile-rate movement.
"""

import sys
import json
import math
import collections


def load(path):
    by_prob = collections.defaultdict(list)
    for line in open(path):
        r = json.loads(line)
        by_prob[r["problem"]].append(r["status"])
    return by_prob


def pass_at_k(n, c, k):
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def main():
    a_path, b_path = sys.argv[1], sys.argv[2]
    A, B = load(a_path), load(b_path)
    probs = sorted(set(A) & set(B))
    only = (set(A) | set(B)) - set(probs)
    if only:
        print(f"[warn] {len(only)} problems present in only one run, "
              f"excluded: {sorted(only)[:5]}...")

    rows = []
    for pb in probs:
        ca, na = A[pb].count("PASS"), len(A[pb])
        cb, nb = B[pb].count("PASS"), len(B[pb])
        compa = sum(s in ("PASS", "fail") for s in A[pb]) / na
        compb = sum(s in ("PASS", "fail") for s in B[pb]) / nb
        rows.append((pb, ca, na, cb, nb, compa, compb))

    for k in (1, 5, 10):
        pa = sum(pass_at_k(n, c, min(k, n)) for _, c, n, _, _, _, _ in rows)
        pb_ = sum(pass_at_k(n, c, min(k, n)) for _, _, _, c, n, _, _ in rows)
        print(f"pass@{k:<2d}: {a_path.split('/')[-1]:24s} "
              f"{100 * pa / len(rows):5.1f}%   "
              f"{b_path.split('/')[-1]:24s} {100 * pb_ / len(rows):5.1f}%   "
              f"delta {100 * (pb_ - pa) / len(rows):+.1f}")
    ca_ = sum(r[5] for r in rows) / len(rows)
    cb_ = sum(r[6] for r in rows) / len(rows)
    print(f"compile: {100 * ca_:.1f}% -> {100 * cb_:.1f}% "
          f"(delta {100 * (cb_ - ca_):+.1f})")

    moved = [r for r in rows if r[1] != r[3]]
    moved.sort(key=lambda r: r[3] - r[1])
    print(f"\n{len(moved)} problems changed pass count "
          f"(negative delta first = broken by run B):")
    print(f"{'problem':32s} {'A':>5s} {'B':>5s} {'delta':>6s}")
    for pb, ca, na, cb, nb, _, _ in moved:
        print(f"{pb:32s} {ca:3d}/{na:<2d} {cb:3d}/{nb:<2d} {cb - ca:+5d}")

    fixed = sum(1 for r in moved if r[3] > r[1] and r[1] == 0)
    broke = sum(1 for r in moved if r[3] < r[1] and r[3] == 0)
    print(f"\nzero->nonzero (B solves problems A never did): "
          f"{sum(1 for r in moved if r[1] == 0 and r[3] > 0)}")
    print(f"nonzero->zero (B lost problems A could do):      "
          f"{sum(1 for r in moved if r[1] > 0 and r[3] == 0)}")


if __name__ == "__main__":
    main()
