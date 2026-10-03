#!/usr/bin/env python3
"""Draw the scaling study's confirmation split with the frozen sealed-split generator.

Reuses ``student/make_dev_split.py`` (the Gate 0 development-split wrapper) with
three declared differences, fixed before the draw:

1. seed 20261003;
2. every design in each ``--exclude-split`` file (at least the Gate 0
   development split) is excluded as well;
3. the median extrapolation pool gains widths 27 and 29 in addition to 23 and 25,
   because earlier splits consumed most of it.

The split is untouched until the confirmation phase of the plan; every corpus
built for the study must exclude it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from student import make_dev_split as M  # noqa: E402

CONFIRM_SEED = 20261003
EXTRA_MED_WIDTHS = (27, 29)


def split_designs(path: str) -> set:
    with open(path, encoding="utf-8") as handle:
        return {row["design"] for row in json.load(handle)["designs"]}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fpga-root", default=None,
                    help="frozen checkout; default: the one Gate 0 used (gate0/plan.json)")
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--exclude-split", nargs="+", required=True)
    ap.add_argument("--also-exclude-from", nargs="*", default=[])
    args = ap.parse_args(argv)

    if args.fpga_root is None:
        with open(os.path.join(os.path.dirname(HERE), "gate0", "plan.json"), encoding="utf-8") as handle:
            args.fpga_root = json.load(handle)["fpga_root"]
    excluded = set()
    for path in args.exclude_split:
        excluded |= split_designs(path)
    original = M.designs_named_under
    M.designs_named_under = lambda root: original(root) | excluded
    M.EXTRA_MED_EXTRAP_WIDTHS = tuple(sorted(set(M.EXTRA_MED_EXTRAP_WIDTHS) | set(EXTRA_MED_WIDTHS)))
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    M.main(["--fpga-root", args.fpga_root, "--tokenizer", args.tokenizer, "--out", out,
            "--seed", str(CONFIRM_SEED), "--also-exclude-from", *args.also_exclude_from])

    with open(out, encoding="utf-8") as handle:
        split = json.load(handle)
    overlap = {row["design"] for row in split["designs"]} & excluded
    if overlap:
        raise SystemExit(f"confirmation split overlaps an excluded split: {sorted(overlap)}")
    split["purpose"] = "Physical-scaling confirmation split; untouched until the confirmation phase"
    split["confirmation_wrapper_sha256"] = M.sha256_file(os.path.abspath(__file__))
    split["excluded_splits"] = [os.path.abspath(p) for p in args.exclude_split]
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(split, handle, indent=1)
        handle.write("\n")
    by_family = {}
    for row in split["designs"]:
        by_family[row["family"]] = by_family.get(row["family"], 0) + 1
    print(f"confirmation split: {len(split['designs'])} designs {by_family}")
    print(f"sha256 {M.sha256_file(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
