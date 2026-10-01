#!/usr/bin/env python3
"""Draw a fresh development split with the frozen sealed-split generator.

Gate 0 must not reuse the sealed 20-design split that carries the submitted
paper's primary result.  This wrapper runs the previous project's
``gen_sealed_split.main`` unchanged except for three declared differences,
fixed before any draw:

1. a new seed (default 20261001);
2. every design in the existing ``sealed_split.json`` and in every
   ``fmax_manifest.json``/``holdout_summary.json`` anywhere under the checkout
   (and under any ``--also-exclude-from`` checkout) is excluded, in addition to
   the generator's own exclusions;
3. the median extrapolation pool gains widths 23 and 25, because the sealed
   split and its follow-ups may have consumed the original pool.

The output keeps schema ``sealed_split/1`` so the frozen loader accepts it,
and records the wrapper's own hash and purpose.  Designs in the dev split must
be excluded from every later training corpus and RL prompt list.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Optional, Sequence

DEV_SEED = 20261001
EXTRA_MED_EXTRAP_WIDTHS = (23, 25)


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read().replace(b"\r\n", b"\n")).hexdigest()


def designs_named_under(root: str) -> set:
    names = set()
    sealed = os.path.join(root, "sealed_split.json")
    if os.path.isfile(sealed):
        with open(sealed, encoding="utf-8") as handle:
            names.update(row["design"] for row in json.load(handle)["designs"])
    for dirpath, _dirs, files in os.walk(root):
        if ".git" in dirpath.split(os.sep):
            continue
        for name in files:
            if name not in ("fmax_manifest.json", "holdout_summary.json"):
                continue
            try:
                with open(os.path.join(dirpath, name), encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, ValueError):
                continue
            if name == "fmax_manifest.json" and isinstance(data, dict):
                names.update(rec["design"] for rec in data.values()
                             if isinstance(rec, dict) and "design" in rec)
            elif isinstance(data, dict):
                for per_policy in data.values():
                    if isinstance(per_policy, dict):
                        names.update(per_policy.keys())
    return names


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fpga-root", required=True)
    ap.add_argument("--tokenizer", required=True,
                    help="tokenizer of the evaluated student family (budget rule)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=DEV_SEED)
    ap.add_argument("--also-exclude-from", nargs="*", default=[],
                    help="other project checkouts whose split, manifests and summaries "
                         "name designs that must also be excluded")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.fpga_root)
    out = os.path.abspath(args.out)
    if os.path.exists(out):
        raise SystemExit(f"{out} exists; a split is drawn once")
    sys.path.insert(0, root)
    os.chdir(root)
    import gen_sealed_split as G

    extra = designs_named_under(root)
    for other in args.also_exclude_from:
        if os.path.isdir(other):
            extra |= designs_named_under(os.path.abspath(other))
    original_used = G.previously_used
    G.previously_used = lambda: original_used() | extra
    widths, variants = G.POOLS["med"]["extrap"]
    G.POOLS["med"]["extrap"] = (sorted(set(widths) | set(EXTRA_MED_EXTRAP_WIDTHS)), variants)

    sys.argv = ["gen_sealed_split.py", "--out", out, "--seed", str(args.seed),
                "--tokenizer", args.tokenizer]
    G.main()

    with open(out, encoding="utf-8") as handle:
        split = json.load(handle)
    split["purpose"] = "Gate-0 development split; not the sealed primary split"
    split["wrapper_sha256"] = sha256_file(os.path.abspath(__file__))
    split["extra_excluded_designs"] = sorted(extra)
    split["med_extrap_widths"] = G.POOLS["med"]["extrap"][0]
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(split, handle, indent=1)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
