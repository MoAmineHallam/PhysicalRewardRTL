#!/usr/bin/env python3
"""Freeze the output-token set for the trimmed-head arm from training data only.

The kept set is the union of tokens in every training completion (generated
RTL), EOS/PAD, and the printable-ASCII fallback tokens.  Evaluation designs
are never read.  ``--exclude-split`` checks that no corpus row names a design
in the evaluation split and refuses to write if one does.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE))

from student.compress import keep_ids_from_texts  # noqa: E402


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read().replace(b"\r\n", b"\n")).hexdigest()


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--corpus", nargs="+", required=True,
                    help="JSONL files with a 'completion' field (SFT/distill corpora)")
    ap.add_argument("--exclude-split", nargs="*", default=[],
                    help="sealed_split/1 files whose designs must not appear in the corpus")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)

    held_out = set()
    for path in args.exclude_split:
        with open(path, encoding="utf-8") as handle:
            held_out.update(row["design"] for row in json.load(handle)["designs"])

    texts, leaks = [], []
    for path in args.corpus:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("design") in held_out:
                    leaks.append(row["design"])
                texts.append(row["completion"])
    if leaks:
        raise SystemExit(f"corpus contains evaluation designs: {sorted(set(leaks))}")

    keep = keep_ids_from_texts(tokenizer, texts)
    head_rows = len(tokenizer)
    out = {
        "schema": "keep_vocab/1",
        "tokenizer": os.path.abspath(args.tokenizer),
        "source": [{"path": os.path.abspath(p), "sha256": sha256_file(p)} for p in args.corpus],
        "n_completions": len(texts),
        "excluded_splits": [os.path.abspath(p) for p in args.exclude_split],
        "tokenizer_size": head_rows,
        "n_keep": len(keep),
        "keep_ids": keep,
    }
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(out, handle, indent=1)
        handle.write("\n")
    print(f"kept {len(keep)} of {head_rows} tokens from {len(texts)} completions -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
