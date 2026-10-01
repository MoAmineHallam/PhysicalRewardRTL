#!/usr/bin/env python3
"""Analytical decode-traffic ledger for a decoder-only student.

For batch-one decoding, every generated token reads all decoder weights, the
output-head rows that are evaluated, and the valid KV cache.  This module
counts those logical bytes from a Hugging Face ``config.json``.  It is a lower
bound on off-chip traffic for a weight-streaming accelerator, not a latency
prediction: caching, refills, ports, and host transfers add cost and must be
measured on the board.
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, Optional, Sequence


def decoder_weight_count(cfg: Dict) -> int:
    """Weights of all attention and MLP projections (biases and norms excluded)."""
    d = cfg["hidden_size"]
    heads = cfg["num_attention_heads"]
    kv_heads = cfg.get("num_key_value_heads", heads)
    head_dim = cfg.get("head_dim", d // heads)
    m = cfg["intermediate_size"]
    attn = d * heads * head_dim * 2 + d * kv_heads * head_dim * 2
    mlp = 3 * d * m
    return cfg["num_hidden_layers"] * (attn + mlp)


def decode_bytes_per_token(cfg: Dict, weight_bits: float = 16.0, group_size: int = 128,
                           scale_bits: int = 16, head_rows: Optional[int] = None,
                           head_bits: float = 16.0, context: int = 0,
                           kv_bits: float = 16.0) -> Dict[str, float]:
    """Logical bytes read per generated token, split by component."""
    d = cfg["hidden_size"]
    heads = cfg["num_attention_heads"]
    kv_heads = cfg.get("num_key_value_heads", heads)
    head_dim = cfg.get("head_dim", d // heads)
    rows = cfg["vocab_size"] if head_rows is None else head_rows
    per_weight = weight_bits + (scale_bits / group_size if weight_bits < 16 else 0.0)
    decoder = decoder_weight_count(cfg) * per_weight / 8
    head = rows * d * head_bits / 8
    kv = context * cfg["num_hidden_layers"] * 2 * kv_heads * head_dim * kv_bits / 8
    return {"decoder_weights": decoder, "output_head": head, "kv_cache": kv,
            "total": decoder + head + kv}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("config", help="model config.json")
    ap.add_argument("--weight-bits", type=float, default=16)
    ap.add_argument("--head-rows", type=int, default=None)
    ap.add_argument("--context", type=int, default=0)
    ap.add_argument("--bandwidth-gbs", type=float, default=None,
                    help="measured sustained bandwidth, for a per-token lower bound")
    args = ap.parse_args(argv)
    with open(args.config, encoding="utf-8") as handle:
        cfg = json.load(handle)
    ledger = decode_bytes_per_token(cfg, args.weight_bits, head_rows=args.head_rows,
                                    context=args.context)
    for key, value in ledger.items():
        print(f"{key:16s} {value / 2**20:10.1f} MiB")
    if args.bandwidth_gbs:
        seconds = ledger["total"] / (args.bandwidth_gbs * 1e9)
        print(f"lower bound      {seconds * 1e3:10.2f} ms/token "
              f"({1 / seconds:.1f} tokens/s) at {args.bandwidth_gbs} GB/s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
