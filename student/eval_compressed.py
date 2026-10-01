#!/usr/bin/env python3
"""Generate one compressed-policy replicate on a frozen design split.

This is the Gate-0 evaluator.  It reuses the previous project's frozen
``eval_sealed`` contract unchanged (sampler, extractor, two-stream oracle,
deduplication with multiplicity, output schema), and adds only a deployment
transform applied after the LoRA adapter is merged:

    FP16 base + adapter --merge--> FP16 model --quantize--> --restrict vocab-->

Outputs match ``eval_sealed`` (``fmax_manifest.json``, ``holdout_summary.json``,
``generation_config.json`` plus one ``.sv`` per distinct oracle-correct
candidate), so the existing Vivado flow and failure-penalized analysis apply.
Run it from any directory; ``--fpga-root`` points at the old ``fpga`` checkout
on the server (the one containing ``eval_sealed.py`` and ``oracle.py``).
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import random
import sys
from types import SimpleNamespace
from typing import Dict, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.dirname(HERE) not in sys.path:
    sys.path.insert(0, os.path.dirname(HERE))

from student.compress import (DEFAULT_TARGETS, quantize_linear_weights_,  # noqa: E402
                              restrict_output_vocabulary_)


def load_fpga_modules(root: str) -> SimpleNamespace:
    """Import the frozen evaluator pieces from the previous project checkout."""
    root = os.path.abspath(root)
    if not os.path.isfile(os.path.join(root, "eval_sealed.py")):
        raise SystemExit(f"--fpga-root {root} does not contain eval_sealed.py")
    if root not in sys.path:
        sys.path.insert(0, root)
    sealed = importlib.import_module("eval_sealed")
    return SimpleNamespace(
        sealed=sealed,
        oracle_score=importlib.import_module("oracle").score,
        extract=importlib.import_module("build_dataset").extract_verilog,
        sample_group=importlib.import_module("grpo_oracle").sample_group,
    )


def load_keep_vocab(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("schema") != "keep_vocab/1" or not data.get("keep_ids"):
        raise SystemExit(f"{path} is not a keep_vocab/1 file with keep_ids")
    return data


def build_model(args: argparse.Namespace):
    """Load, merge, and compress the policy exactly as it will be evaluated."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    if torch.cuda.is_available():
        dtype, device_map = torch.float16, {"": 0}
    elif args.allow_cpu:
        dtype, device_map = torch.float32, {"": "cpu"}
    else:
        raise SystemExit("no CUDA device; pass --allow-cpu only for smoke tests")
    model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=dtype, device_map=device_map)
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False)
        model = model.merge_and_unload()
    model.eval()

    compression: Dict[str, object] = {"weight_bits": args.bits,
                                      "group_size": args.group_size}
    if args.bits < 16:
        compression["quantization"] = quantize_linear_weights_(
            model, args.bits, args.group_size, DEFAULT_TARGETS)
    keep = load_keep_vocab(args.keep_vocab)
    if keep is not None:
        restrict_output_vocabulary_(model, keep["keep_ids"])
        head_rows = model.get_output_embeddings().weight.shape[0]
        compression["output_vocabulary"] = {
            "kept_rows": len(keep["keep_ids"]), "head_rows": head_rows,
            "source": keep.get("source"), "file": os.path.abspath(args.keep_vocab)}
    return model, tokenizer, compression


def run(args: argparse.Namespace, deps: Optional[SimpleNamespace] = None) -> None:
    deps = deps or load_fpga_modules(args.fpga_root)
    sealed = deps.sealed
    if args.n <= 0 or args.n_stim != sealed.DEFAULT_ORACLE_N:
        raise SystemExit(f"requires n>0 and n_stim={sealed.DEFAULT_ORACLE_N}")
    if args.temp != 1.0 or args.gen_batch != 4:
        raise SystemExit("frozen sampling requires temperature 1.0 and batch 4")
    if args.adapter and not os.path.isdir(args.adapter):
        raise SystemExit(f"adapter directory is missing: {args.adapter}")
    sealed.prepare_output(args.out_dir)
    rows = sealed.load_split(args.split)

    import numpy as np
    import torch

    random.seed(args.generation_seed)
    np.random.seed(args.generation_seed)
    torch.manual_seed(args.generation_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.generation_seed)

    model, tokenizer, compression = build_model(args)
    device = next(model.parameters()).device

    manifest: Dict[str, dict] = {}
    summary: Dict[str, Dict[str, dict]] = {args.policy: {}}
    print(f"compressed evaluation: policy={args.policy} bits={args.bits} "
          f"vocab={'restricted' if args.keep_vocab else 'full'} n={args.n}", flush=True)
    for split_row in rows:
        design = split_row["design"]
        _ids, sampled = deps.sample_group(
            model, tokenizer, split_row["prompt"], args.n, args.temp,
            int(split_row["max_tokens"]), device, args.gen_batch)
        texts = [text for _ids, text in sampled]
        if len(texts) != args.n:
            raise SystemExit(f"generator returned {len(texts)} samples for {design}")
        distinct, design_summary = sealed.gate_samples(
            texts, design, args.n, deps.extract, deps.oracle_score,
            oracle_n=args.n_stim)
        design_summary.update({"family": split_row["family"],
                               "regime": split_row["regime"],
                               "max_tokens": int(split_row["max_tokens"])})
        summary[args.policy][design] = design_summary
        index = 0
        for candidate in distinct.values():
            if not candidate["correct"]:
                continue
            module = f"{args.policy}__{design}__g{index}"
            index += 1
            emitted = sealed.rename_module(candidate["rtl"], design, module)
            path = os.path.join(args.out_dir, module + ".sv")
            with open(path, "w", encoding="ascii", newline="\n") as handle:
                handle.write(emitted if emitted.endswith("\n") else emitted + "\n")
            manifest[module] = {
                "policy": args.policy, "design": design,
                "family": split_row["family"], "regime": split_row["regime"],
                "count": candidate["count"], "n": args.n,
                "generation_seed": args.generation_seed,
                "oracle_seeds": list(sealed.ORACLE_SEEDS), "oracle_n": args.n_stim,
                "source_sha256": sealed.sha256_text(candidate["rtl"]),
                "emitted_sha256": sealed.sha256_file(path),
            }
        print(f"  {design:18s} correct={design_summary['n_correct']:2d}/{args.n} "
              f"distinct={design_summary['n_distinct_correct']:2d}", flush=True)

    config = {
        "schema": "compressed_evaluation/1",
        "policy": args.policy,
        "generation_seed": args.generation_seed,
        "n_per_design": args.n,
        "temperature": args.temp,
        "gen_batch": args.gen_batch,
        "oracle_seeds": list(sealed.ORACLE_SEEDS),
        "oracle_n": args.n_stim,
        "base": os.path.abspath(args.base),
        "adapter": os.path.abspath(args.adapter) if args.adapter else None,
        "adapter_sha256": sealed.sha256_dir(args.adapter) if args.adapter else None,
        "split": os.path.abspath(args.split),
        "split_sha256": sealed.sha256_file(args.split),
        "compression": compression,
        "keep_vocab_sha256": (sealed.sha256_file(args.keep_vocab)
                              if args.keep_vocab else None),
        "eval_script_sha256": sealed.sha256_file(os.path.abspath(__file__)),
        "compress_sha256": sealed.sha256_file(os.path.join(HERE, "compress.py")),
        "frozen_evaluator_sha256": sealed.sha256_file(os.path.abspath(sealed.__file__)),
        "torch": torch.__version__,
        "device": (torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"),
    }
    for name, payload in (("fmax_manifest.json", manifest),
                          ("holdout_summary.json", summary),
                          ("generation_config.json", config)):
        with open(os.path.join(args.out_dir, name), "w", encoding="utf-8",
                  newline="\n") as handle:
            json.dump(payload, handle, indent=1)
            handle.write("\n")
    print(f"wrote {len(manifest)} distinct correct candidates -> {args.out_dir}")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fpga-root", required=True,
                    help="previous project checkout containing eval_sealed.py")
    ap.add_argument("--base", required=True, help="base model directory")
    ap.add_argument("--adapter", default=None, help="LoRA adapter; omit for the base model")
    ap.add_argument("--split", required=True, help="sealed_split/1 design split")
    ap.add_argument("--policy", required=True, help="output tag, [a-z][a-z0-9_]*")
    ap.add_argument("--generation-seed", type=int, required=True)
    ap.add_argument("--n", type=int, required=True, help="draws per design")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--bits", type=int, default=16, choices=(16, 8, 6, 5, 4, 3),
                    help="weight bits for decoder linear layers; 16 = unchanged")
    ap.add_argument("--group-size", type=int, default=128)
    ap.add_argument("--keep-vocab", default=None,
                    help="keep_vocab/1 JSON from make_keep_vocab.py")
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--gen-batch", type=int, default=4)
    ap.add_argument("--n-stim", type=int, default=1024)
    ap.add_argument("--allow-cpu", action="store_true", help="smoke tests only")
    return ap


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    import re
    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.policy):
        raise SystemExit("policy tag must match [a-z][a-z0-9_]*")
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
