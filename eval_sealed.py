#!/usr/bin/env python3
"""Generate one frozen policy replicate on the prospective sealed split.

This evaluator intentionally handles exactly one adapter and one sampling seed
per invocation.  Separate directories are therefore separate experimental
replicates; a failed invocation cannot leave a mixture of policies or seeds in
one manifest.

The script only emits oracle-correct, distinct RTL modules for Vivado.  The
manifest retains their sample multiplicities, while ``holdout_summary.json``
records the total sample count for every design, including designs with zero
correct candidates.  Downstream analysis consequently scores every incorrect,
extraction-failed, and implementation-failed sample as zero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sys
from collections import OrderedDict
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence


HERE = os.path.dirname(os.path.abspath(__file__))
ORACLE_SEEDS = (1, 2)
DEFAULT_ORACLE_N = 1024


class EvaluationError(RuntimeError):
    """An input or output violates the frozen evaluation contract."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.replace("\r\n", "\n").encode()).hexdigest()


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        raw = handle.read()
    if os.path.splitext(path)[1].lower() in {
            ".py", ".json", ".jsonl", ".md", ".sv", ".v", ".tcl", ".txt", ".sh"}:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def sha256_dir(root: str) -> str:
    entries = []
    for dirpath, _dirs, files in os.walk(root):
        for name in sorted(files):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            entries.append((rel, sha256_file(path)))
    digest = hashlib.sha256()
    for rel, file_hash in sorted(entries):
        digest.update(rel.encode() + b"\0" + file_hash.encode() + b"\n")
    return digest.hexdigest()


def load_split(path: str) -> List[dict]:
    try:
        with open(path, encoding="utf-8") as handle:
            split = json.load(handle)
    except (OSError, ValueError) as exc:
        raise EvaluationError(f"cannot read sealed split {path}: {exc}") from exc
    if split.get("schema") != "sealed_split/1":
        raise EvaluationError(f"unexpected sealed schema: {split.get('schema')!r}")
    rows = split.get("designs")
    if not isinstance(rows, list) or len(rows) != int(split.get("n_designs", -1)):
        raise EvaluationError("sealed split design count is missing or inconsistent")
    seen = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise EvaluationError(f"sealed design row {index} is not an object")
        required = ("design", "family", "regime", "prompt", "prompt_sha256",
                    "max_tokens")
        if any(row.get(key) in (None, "") for key in required):
            raise EvaluationError(f"sealed design row {index} lacks a required field")
        design = row["design"]
        if design in seen:
            raise EvaluationError(f"duplicate sealed design: {design}")
        seen.add(design)
        if row["regime"] not in ("interp", "extrap"):
            raise EvaluationError(f"invalid regime for {design}: {row['regime']}")
        if sha256_text(row["prompt"]) != row["prompt_sha256"]:
            raise EvaluationError(f"prompt hash mismatch for {design}")
        if int(row["max_tokens"]) <= 0:
            raise EvaluationError(f"invalid token budget for {design}")
    return rows


def normalised_rtl(rtl: str) -> str:
    body = re.sub(r"\bmodule\s+\w+", "module M", rtl, count=1)
    return re.sub(r"\s+", " ", body).strip()


def rename_module(rtl: str, design: str, module: str) -> str:
    out, count = re.subn(r"\bmodule\s+" + re.escape(design) + r"\b",
                         "module " + module, rtl, count=1)
    if count != 1:
        raise EvaluationError(
            f"oracle-correct RTL for {design} did not contain its module declaration")
    return out


def prepare_output(directory: str) -> None:
    if os.path.exists(directory):
        entries = os.listdir(directory) if os.path.isdir(directory) else [directory]
        if entries:
            raise EvaluationError(
                f"output {directory} is not empty; move a failed replicate aside, "
                "never merge or resume it")
    else:
        os.makedirs(directory)


def gate_samples(
        texts: Iterable[str], design: str, n_samples: int,
        extract: Callable[[str, str], Optional[str]],
        score: Callable[..., Mapping[str, Any]],
        reward_fn: Optional[Callable[[str], tuple]] = None,
        oracle_n: int = DEFAULT_ORACLE_N) -> tuple[OrderedDict, dict]:
    """Deduplicate, oracle-check, and optionally RF-score one design's samples."""
    distinct: OrderedDict[str, dict] = OrderedDict()
    extraction_failures = 0
    for text in texts:
        rtl = extract(text, design)
        if rtl is None:
            extraction_failures += 1
            continue
        rtl = rtl.encode("ascii", "replace").decode("ascii")
        key = normalised_rtl(rtl)
        if key not in distinct:
            distinct[key] = {"rtl": rtl, "count": 0}
        distinct[key]["count"] += 1

    if extraction_failures + sum(row["count"] for row in distinct.values()) != n_samples:
        raise EvaluationError(f"sample accounting failed for {design}")

    correct_samples = oracle_errors = compiled_samples = 0
    for row in distinct.values():
        verdicts = []
        try:
            for seed in ORACLE_SEEDS:
                verdicts.append(score(row["rtl"], design, n=oracle_n, seed=seed))
        except Exception as exc:  # recorded as a failed sample, never silently passed
            row.update({"correct": False, "compiled": False,
                        "oracle_error": f"{type(exc).__name__}: {exc}"[:300]})
            oracle_errors += row["count"]
            continue
        compiled = all(bool(v.get("compiled")) for v in verdicts)
        correct = all(bool(v.get("correct")) for v in verdicts)
        row.update({"correct": correct, "compiled": compiled})
        if compiled:
            compiled_samples += row["count"]
        if not correct:
            continue
        correct_samples += row["count"]
        if reward_fn is not None:
            reward, meta = reward_fn(row["rtl"])
            row["reward"] = float(reward)
            row["reward_gate"] = meta.get("gate")
            row["reward_gate_detail"] = meta.get("detail")
            row["canon_hash"] = meta.get("canon_hash")

    summary = {
        "n": n_samples,
        "n_extraction_failed": extraction_failures,
        "n_oracle_error": oracle_errors,
        "n_compiled": compiled_samples,
        "n_correct": correct_samples,
        "correct_pct": 100.0 * correct_samples / n_samples,
        "n_distinct_extracted": len(distinct),
        "n_distinct_correct": sum(1 for row in distinct.values() if row["correct"]),
    }
    return distinct, summary


def run(args: argparse.Namespace) -> None:
    if args.n <= 0 or args.n_stim != DEFAULT_ORACLE_N:
        raise EvaluationError(
            f"frozen evaluation requires n>0 and n_stim={DEFAULT_ORACLE_N}")
    if args.temp != 1.0 or args.gen_batch != 4:
        raise EvaluationError("frozen evaluation requires temperature 1.0 and batch 4")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", args.policy):
        raise EvaluationError("policy tag must match [a-z][a-z0-9_]*")
    if not os.path.isdir(args.adapter):
        raise EvaluationError(f"adapter directory is missing: {args.adapter}")
    prepare_output(args.out_dir)
    rows = load_split(args.sealed)

    import numpy as np
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import oracle
    from build_dataset import extract_verilog
    from grpo_oracle import load_rf_struct, sample_group

    random.seed(args.generation_seed)
    np.random.seed(args.generation_seed)
    torch.manual_seed(args.generation_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.generation_seed)

    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.float16, device_map={"": 0})
    model = PeftModel.from_pretrained(
        base, args.adapter, is_trainable=False).eval()
    device = next(model.parameters()).device
    reward_fn = load_rf_struct(args.rf) if args.score_rf else None

    manifest: Dict[str, dict] = {}
    summary: Dict[str, Dict[str, dict]] = {args.policy: {}}
    print(f"sealed evaluation: policy={args.policy} n={args.n}/design "
          f"generation_seed={args.generation_seed}", flush=True)
    for split_row in rows:
        design = split_row["design"]
        _prompt_ids, sampled = sample_group(
            model, tokenizer, split_row["prompt"], args.n, args.temp,
            int(split_row["max_tokens"]), device, args.gen_batch)
        texts = [text for _ids, text in sampled]
        if len(texts) != args.n:
            raise EvaluationError(
                f"generator returned {len(texts)} samples for {design}; expected {args.n}")
        distinct, design_summary = gate_samples(
            texts, design, args.n, extract_verilog, oracle.score,
            reward_fn=reward_fn, oracle_n=args.n_stim)
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
            emitted = rename_module(candidate["rtl"], design, module)
            path = os.path.join(args.out_dir, module + ".sv")
            with open(path, "w", encoding="ascii", newline="\n") as handle:
                handle.write(emitted)
                if not emitted.endswith("\n"):
                    handle.write("\n")
            record = {
                "policy": args.policy, "design": design,
                "family": split_row["family"], "regime": split_row["regime"],
                "count": candidate["count"], "n": args.n,
                "generation_seed": args.generation_seed,
                "oracle_seeds": list(ORACLE_SEEDS), "oracle_n": args.n_stim,
                "source_sha256": sha256_text(candidate["rtl"]),
                "emitted_sha256": sha256_file(path),
            }
            for key in ("reward", "reward_gate", "reward_gate_detail", "canon_hash"):
                if candidate.get(key) is not None:
                    record[key] = candidate[key]
            manifest[module] = record
        print(f"  {design:18s} correct={design_summary['n_correct']:2d}/{args.n} "
              f"distinct={design_summary['n_distinct_correct']:2d}", flush=True)

    config = {
        "schema": "sealed_evaluation/1",
        "policy": args.policy,
        "training_seed": args.training_seed,
        "generation_seed": args.generation_seed,
        "n_per_design": args.n,
        "temperature": args.temp,
        "gen_batch": args.gen_batch,
        "oracle_seeds": list(ORACLE_SEEDS),
        "oracle_n": args.n_stim,
        "score_rf": bool(args.score_rf),
        "base": os.path.abspath(args.base),
        "adapter": os.path.abspath(args.adapter),
        "adapter_sha256": sha256_dir(args.adapter),
        "sealed_split": os.path.abspath(args.sealed),
        "sealed_split_sha256": sha256_file(args.sealed),
        "eval_script_sha256": sha256_file(os.path.abspath(__file__)),
        "rf_artifact_sha256": sha256_file(args.rf) if args.score_rf else None,
        "torch": torch.__version__,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }
    with open(os.path.join(args.out_dir, "fmax_manifest.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=1)
        handle.write("\n")
    with open(os.path.join(args.out_dir, "holdout_summary.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        json.dump(summary, handle, indent=1)
        handle.write("\n")
    with open(os.path.join(args.out_dir, "generation_config.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        json.dump(config, handle, indent=1)
        handle.write("\n")
    print(f"wrote {len(manifest)} distinct correct candidates -> {args.out_dir}")


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--sealed", default=os.path.join(HERE, "sealed_split.json"))
    ap.add_argument("--policy", required=True)
    ap.add_argument("--training-seed", type=int, required=True,
                    help="0 for SFT, otherwise the matching policy-training seed")
    ap.add_argument("--generation-seed", type=int, required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--temp", type=float, default=1.0)
    ap.add_argument("--gen-batch", type=int, default=4)
    ap.add_argument("--n-stim", type=int, default=DEFAULT_ORACLE_N)
    ap.add_argument("--score-rf", action="store_true")
    ap.add_argument("--rf", default="rf_struct.joblib")
    return ap


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        run(parser().parse_args(argv))
    except EvaluationError as exc:
        print(f"sealed evaluation error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
