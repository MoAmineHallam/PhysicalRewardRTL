#!/usr/bin/env python3
"""
gen_fmax_candidates.py  -  Stage 4 prep: does the SFT policy emit Fmax-DIVERSE
correct implementations? (the RL-headroom gate) + seed data for the surrogate.

With SFT competence at ~90-100% (probe_competence), GRPO's optimisation signal is
the Fmax SPREAD among correct candidates, not correctness. This generates, per
design, many oracle-VERIFIED-correct candidates with the SFT adapter (corpus-
format prompts), DEDUPES identical implementations, and renames each surviving
module to <design>__g<k> so run_ppa (top = filename stem) can synthesise it for
Vivado Fmax. The resulting Fmax range per design = the headroom GRPO can exploit;
the (RTL -> Fmax) pairs are also the first training data for the Stage-3 surrogate.

Server (GPU + iverilog):
    python gen_fmax_candidates.py --adapter sft_v3_out --n 40 --keep 12
Laptop (Vivado):
    python run_ppa.py --dir rtl/fmax_probe --out rtl/fmax_probe/ppa.jsonl \
        --clk clk --period 5.0 --vivado "C:\\Xilinx\\Vivado\\2023.1\\bin\\vivado.bat"
Anywhere:
    python analyze_accel_spread.py  (point it at rtl/fmax_probe)
"""

import os
import re
import json
import argparse

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

import oracle
from build_dataset import extract_verilog
from probe_competence import probe_prompts, generate

HERE = os.path.dirname(os.path.abspath(__file__))
# fir/firr/poly only -- the families SFT made competent (cordic excluded).
DEFAULT_DESIGNS = ["fir8_8b", "fir16_8b", "fir32_8b", "firr8", "firr16",
                   "poly4_8b", "poly6_8b", "poly8_v3_8b"]


def norm(rtl):
    """Implementation identity = body with module name and whitespace stripped."""
    body = re.sub(r"\bmodule\s+\w+", "module M", rtl, count=1)
    return re.sub(r"\s+", " ", body).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get(
        "RTLCODER_PATH", "/zeng_gk/Amine/mas/rtlcoder"))
    ap.add_argument("--adapter", default="sft_v3_out")
    ap.add_argument("--designs", nargs="*", default=DEFAULT_DESIGNS)
    ap.add_argument("--n", type=int, default=40, help="generations per design")
    ap.add_argument("--keep", type=int, default=12,
                    help="max DISTINCT correct impls kept per design")
    ap.add_argument("--temp", type=float, default=0.9)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--out-dir", default=os.path.join(HERE, "rtl", "fmax_probe"))
    args = ap.parse_args()

    prompts = probe_prompts(set(args.designs))
    os.makedirs(args.out_dir, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.float16, device_map={"": 0})
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False)
    model.eval()

    mani, tot = {}, 0
    for name, (fam, prompt) in prompts.items():
        texts = generate(model, tok, prompt, args.n, args.temp, args.max_tokens)
        seen, kept = set(), 0
        for t in texts:
            if kept >= args.keep:
                break
            rtl = extract_verilog(t, name)
            if rtl is None:
                continue
            rtl = rtl.encode("ascii", "replace").decode("ascii")
            key = norm(rtl)
            if key in seen:
                continue
            try:
                r = oracle.score(rtl, name)
            except Exception:
                continue
            if not r["correct"]:
                continue
            seen.add(key)
            mod = f"{name}__g{kept}"
            rr = re.sub(r"\bmodule\s+" + re.escape(name) + r"\b",
                        "module " + mod, rtl, count=1)
            with open(os.path.join(args.out_dir, mod + ".sv"), "w") as f:
                f.write(rr)
            mani[mod] = {"design": name, "family": fam}
            kept += 1
        tot += kept
        print(f"  {name:12s} ({fam:5s})  kept {kept:2d} distinct-correct / {args.n}",
              flush=True)

    json.dump(mani, open(os.path.join(args.out_dir, "fmax_manifest.json"), "w"),
              indent=1)
    print(f"\n{tot} distinct-correct candidates across {len(prompts)} designs "
          f"-> {args.out_dir}")
    print("next (laptop, Vivado): run_ppa.py --dir rtl/fmax_probe ... then look at "
          "the Fmax range PER design -> that spread is the GRPO headroom + the "
          "first (RTL->Fmax) data for the Stage-3 surrogate.")


if __name__ == "__main__":
    main()
