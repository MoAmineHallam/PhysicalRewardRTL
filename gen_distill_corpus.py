#!/usr/bin/env python3
"""
gen_distill_corpus.py  -  Phase D+ step 1: oracle-filtered distillation corpus.

Samples the GRPO policy (grpo_v8_cont; fallback grpo_v7) over ALL train-split
designs and keeps ONLY oracle-verified-correct completions (invariant #1
applies to distillation data too -- the oracle filter is what makes this
distillation unusually clean). Dedup by norm() so the student sees each
distinct implementation once. Output rows are the exact sft_corpus.jsonl
format ({design, family, style, prompt, completion}), so sft_train_v2.py
trains the 1.5B student on it with zero changes.

Held-out isolation (invariant #3): designs default to the train split only,
and a hard guard refuses to run if any frozen §5 held-out design is passed.

Server (AFTER grpo_v8_cont frees a GPU; never alongside a 7B training run --
the box's memory cgroup OOM-killed grpo_v8 once already):
    CUDA_VISIBLE_DEVICES=0 nohup python gen_distill_corpus.py \
        --adapter grpo_v8_cont --n 24 > distill_corpus.log 2>&1 &

Resumable: designs already present in --out are skipped; safe to re-launch.
"""

import os
import json
import argparse

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

import oracle
import gen_sft_corpus as GSC
from build_dataset import extract_verilog
from probe_competence import probe_prompts, generate
from gen_fmax_candidates import norm

HERE = os.path.dirname(os.path.abspath(__file__))


def train_designs():
    """All train-split designs (mirrors grpo_oracle.train_split_designs, but
    without importing its heavy module graph). cordic stays out (7B ceiling)."""
    return [name for name, fam, _, _ in GSC.designs(exclude_holdout=True)
            if fam != "cordic"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--adapter", default="grpo_v8_cont",
                    help="GRPO policy to distill (fallback: grpo_v7)")
    ap.add_argument("--designs", nargs="*", default=None,
                    help="default = ALL train-split designs")
    ap.add_argument("--n", type=int, default=24, help="samples per design")
    ap.add_argument("--temp", type=float, default=1.0,
                    help="match the eval protocol (diversity for the student)")
    ap.add_argument("--max-tokens", type=int, default=1536)
    ap.add_argument("--oracle-n", type=int, default=512,
                    help="oracle stimulus length (train-time gate, seed 0)")
    ap.add_argument("--out", default=os.path.join(HERE, "distill_corpus.jsonl"))
    args = ap.parse_args()

    designs = args.designs or train_designs()
    leaked = [d for d in designs if GSC.is_holdout(d)]
    if leaked:
        raise SystemExit(f"HELD-OUT LEAK into distillation designs: {leaked} "
                         "-- the student must never see the frozen §5 split")

    done = set()
    if os.path.exists(args.out):
        with open(args.out) as f:
            done = {json.loads(l)["design"] for l in f if l.strip()}
        print(f"[resume] {len(done)} designs already in {args.out}")

    prompts = probe_prompts(set(designs))
    todo = {nm: v for nm, v in prompts.items() if nm not in done}
    print(f"distilling {args.adapter}: {len(todo)}/{len(prompts)} designs to "
          f"sample ({args.n}/design, temp {args.temp})", flush=True)

    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.float16, device_map={"": 0})
    from peft import PeftModel
    model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False)
    model.eval()

    tot_kept = tot_gen = 0
    for name, (fam, prompt) in sorted(todo.items()):
        texts = generate(model, tok, prompt, args.n, args.temp, args.max_tokens)
        seen, rows = set(), []
        for t in texts:
            rtl = extract_verilog(t, name)
            if rtl is None:
                continue
            rtl = rtl.encode("ascii", "replace").decode("ascii")
            key = norm(rtl)
            if key in seen:
                continue
            try:
                r = oracle.score(rtl, name, n=args.oracle_n)
            except Exception:
                continue
            if not r["correct"]:
                continue
            seen.add(key)
            rows.append({"design": name, "family": fam, "style": "distill",
                         "prompt": prompt, "completion": rtl})
        # append per design -> resumable at design granularity
        with open(args.out, "a") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        tot_kept += len(rows)
        tot_gen += args.n
        print(f"  {name:14s} ({fam:5s}) kept {len(rows):2d} distinct-correct "
              f"/ {args.n}", flush=True)

    print(f"\ndistill corpus: +{tot_kept} rows this run "
          f"(from {tot_gen} samples) -> {args.out}")
    print("next: sft_train_v2.py on the 1.5B student (ModelScope download at "
          "/zeng_gk/Amine/mas/models), unchanged recipe; then "
          "probe_competence -> eval_holdout -> laptop run_ppa for the "
          "student money-table row.")


if __name__ == "__main__":
    main()
