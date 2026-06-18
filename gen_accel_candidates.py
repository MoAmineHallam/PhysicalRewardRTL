#!/usr/bin/env python3
"""
gen_accel_candidates.py  -  Phase-3 generation-diversity probe / RL dataset gen.
Runs ON the server (GPU + iverilog).

Samples the base RTLCoder N times per accelerator spec and keeps the
functionally-CORRECT generations (score_accel vs the design's golden.py). The
probe question: does the base model actually GENERATE Fmax-diverse correct
implementations of a spec? If yes, the silicon-Fmax RL has signal to exploit;
if every correct generation is the same implementation, it does not (and the
robust deliverable is best-of-N reranking instead). Either way these same
correct candidates are the RL dataset.

Each kept candidate's module is renamed to a unique <design>__g<k> so run_ppa
(top = filename stem) can synthesise it for Vivado Fmax.

Run from /zeng_gk/Amine/mas:
    python fpga/gen_accel_candidates.py --n 24
Then on the laptop (Vivado):
    python run_ppa.py --dir fpga/rtl/accel_probe \
        --out fpga/rtl/accel_probe/ppa.jsonl --clk clk --period 5.0 \
        --vivado "C:\\Xilinx\\Vivado\\2023.1\\bin\\vivado.bat"
Then anywhere:
    python fpga/analyze_accel_spread.py
"""

import os
import re
import json
import argparse

os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

import score_accel as SA
from build_dataset import make_prompt, extract_verilog, LLM_DIR

HERE = os.path.dirname(os.path.abspath(__file__))
ACCEL_RE = re.compile(r"^(fir\d+_8b|poly\d+_8b|cordic\d+)$")


def accel_designs():
    out = []
    for d in sorted(os.listdir(SA.RTL_LIB)):
        if not ACCEL_RE.match(d):
            continue
        dd = os.path.join(SA.RTL_LIB, d)
        if os.path.exists(os.path.join(dd, "golden.py")) and \
           os.path.exists(os.path.join(dd, "spec.txt")):
            out.append(d)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default=None, help="LoRA dir (omit = base)")
    ap.add_argument("--designs", nargs="*", default=None)
    ap.add_argument("--n", type=int, default=24, help="generations per design")
    ap.add_argument("--temp", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--min-reward", type=float, default=0.999)
    ap.add_argument("--out-dir", default=os.path.join(HERE, "rtl", "accel_probe"))
    ap.add_argument("--base_model",
                    default=os.environ.get("RTLCODER_PATH",
                                           os.path.join(LLM_DIR, "rtlcoder")))
    args = ap.parse_args()

    designs = args.designs or accel_designs()
    os.makedirs(args.out_dir, exist_ok=True)
    print(f"designs ({len(designs)}): {', '.join(designs)}", flush=True)

    tok = AutoTokenizer.from_pretrained(args.base_model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model, torch_dtype=torch.float16, device_map={"": 0})
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter, is_trainable=False)
    model.eval()

    mani = {}
    tot = 0
    for d in designs:
        spec = open(os.path.join(SA.RTL_LIB, d, "spec.txt")).read()
        prompt = make_prompt({"name": d}, spec) + SA.V2001_SUFFIX
        chat = tok.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=False, add_generation_prompt=True)
        inp = tok(chat, return_tensors="pt",
                  return_token_type_ids=False).to("cuda:0")
        with torch.inference_mode():
            out = model.generate(
                **inp, max_new_tokens=args.max_tokens, do_sample=True,
                temperature=args.temp, num_return_sequences=args.n,
                pad_token_id=tok.eos_token_id)
        # NOTE: no stop_strings -- it detokenises every sequence on the CPU each
        # step (GPU idles at 0%, crawls for num_return_sequences>>1). We generate
        # the full length at full GPU util; extract_verilog truncates at endmodule.
        plen = inp["input_ids"].shape[1]
        kept = 0
        rewards = []
        for seq in out:
            txt = tok.decode(seq[plen:], skip_special_tokens=True)
            rtl = extract_verilog(txt, d)
            if rtl is None:
                continue
            rtl = rtl.encode("ascii", errors="replace").decode("ascii")
            try:
                rew = SA.score_rtl(rtl, d)
            except Exception:
                continue
            rewards.append(round(rew, 3))
            if rew < args.min_reward:
                continue
            mod = f"{d}__g{kept}"
            rr = re.sub(r"\bmodule\s+" + re.escape(d) + r"\b",
                        "module " + mod, rtl, count=1)
            with open(os.path.join(args.out_dir, mod + ".sv"), "w") as f:
                f.write(rr)
            mani[mod] = {"design": d, "family": ACCEL_RE.match(d).group(1)[:3]}
            kept += 1
        tot += kept
        print(f"{d:10s} kept {kept}/{args.n} correct  "
              f"(rewards: {sorted(set(rewards), reverse=True)[:6]})", flush=True)

    json.dump(mani, open(os.path.join(args.out_dir, "probe_manifest.json"), "w"),
              indent=1)
    print(f"\n{tot} correct candidates across {len(designs)} designs -> "
          f"{args.out_dir}\nnext: run_ppa on this dir, then analyze_accel_spread.py")


if __name__ == "__main__":
    main()
