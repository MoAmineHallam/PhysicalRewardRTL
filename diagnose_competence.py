#!/usr/bin/env python3
"""
diagnose_competence.py  -  why do poly/cordic still fail after SFT?

The competence probe showed SFT works for fir/firr (~60-70%) but poly stays ~3%
(compiles but wrong) and cordic ~0% (won't even compile). This dumps, per design,
the diagnostic detail needed to tell WHICH failure mode it is:

  * endmodule-rate of the RAW generations -> distinguishes "ran out of tokens"
    (truncated, no endmodule) from "wrote wrong code";
  * oracle match-fraction distribution over compiled candidates -> distinguishes
    "off by latency/a few coeffs" (match high but < 0.999) from "structurally
    wrong" (match ~ random);
  * the actual RTL of the best-but-incorrect compiled candidate, to eyeball.

    python diagnose_competence.py --adapter sft_v2_out --designs poly3_8b cordic8
"""

import os
import argparse

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

import gen_sft_corpus as GSC
import oracle
from build_dataset import extract_verilog
from probe_competence import probe_prompts, generate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--adapter", default="sft_v2_out")
    ap.add_argument("--designs", nargs="*", default=["poly3_8b", "cordic8"])
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=1536)
    args = ap.parse_args()

    prompts = probe_prompts(set(args.designs))
    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.float16, device_map={"": 0})
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False)
    model.eval()

    for name, (fam, prompt) in prompts.items():
        print(f"\n############## {name} ({fam}) "
              f"max_tokens={args.max_tokens} ##############")
        texts = generate(model, tok, prompt, args.n, args.temp, args.max_tokens)
        has_end = sum("endmodule" in t for t in texts)
        print(f"raw generations: {len(texts)}, contain 'endmodule': "
              f"{has_end}/{len(texts)}  (low -> truncated / ran out of tokens)")
        scored = []
        for t in texts:
            rtl = extract_verilog(t, name)
            if rtl is None:
                continue
            rtl = rtl.encode("ascii", "replace").decode("ascii")
            try:
                r = oracle.score(rtl, name)
            except Exception as e:
                r = {"compiled": False, "match": 0.0, "latency": -1,
                     "correct": False, "err": str(e)[:60]}
            scored.append((r, rtl))
        comp = [s for s in scored if s[0]["compiled"]]
        print(f"extracted: {len(scored)}, compiled: {len(comp)}")
        if comp:
            matches = sorted((s[0]["match"] for s in comp), reverse=True)
            print(f"compiled match-fractions (desc): "
                  f"{[round(m,3) for m in matches]}")
            # best-but-incorrect compiled candidate
            wrong = [s for s in comp if not s[0]["correct"]]
            if wrong:
                best = max(wrong, key=lambda s: s[0]["match"])
                print(f"\n--- best INCORRECT compiled (match={best[0]['match']}, "
                      f"latency={best[0]['latency']}) ---")
                print(best[1][:1800])
        else:
            # nothing compiled: show one raw generation tail to see truncation
            print("\n--- one raw generation (tail 800 chars) ---")
            print(texts[0][-800:])


if __name__ == "__main__":
    main()
